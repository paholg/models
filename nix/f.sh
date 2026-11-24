# Pick a design with fzf, then act on it with single keys. A design is a
# build123d project (a .py file among them), which becomes Orca projects, or a
# script in gcode/, which writes G-code.
cd "$(git rev-parse --show-toplevel)" || exit

# Moonraker and Fluidd on the printer.
PRINTER="${PRINTER:-10.0.0.15}"

# Map each changed file to its git status in $marks, in the symbols starship
# uses: = conflicted, » renamed, ! modified, + staged, ? untracked.
declare -A marks
git_marks() {
  local line xy mark
  marks=()
  while IFS= read -r -d '' line; do
    xy="${line:0:2}"
    case "$xy" in
      '??') mark='?' ;;
      DD | AU | UD | UA | DU | AA | UU) mark='=' ;;
      *)
        mark=""
        if [[ $xy == *R* ]]; then mark+='»'; fi
        if [[ ${xy:1:1} == [MT] ]]; then mark+='!'; fi
        if [[ ${xy:0:1} == [MAT] ]]; then mark+='+'; fi
        ;;
    esac
    if [[ -n $mark ]]; then
      marks["${line:3}"]="$mark"
    fi
    # A rename or copy is followed by the path it came from.
    if [[ $xy == *[RC]* ]]; then
      IFS= read -r -d '' _ || true
    fi
  done < <(git status --porcelain -z --untracked-files=all)
}

# Pick a design into $file and its $kind (cad or gcode), starting from the query $1.
pick() {
  local files rows list path row mark longest width cols margin
  files="$({
    # A project is told from any other script by what it imports.
    fd --extension py --exclude python --exclude gcode \
      --exec-batch grep --files-with-matches '^from build\.cad import' |
      sed 's|^\./||' || true
    fd --extension py . gcode
  } | sort)"
  # Show path components as aligned columns, without the suffix;
  # the real path rides along in a hidden first field.
  rows="$(echo "$files" | sed -E 's/\.py$//' | column -t -s/ -o '  ')"
  # Each file's git status goes in a last column.
  git_marks
  width="$(echo "$rows" | wc -L)"
  longest=0
  list=""
  while IFS=$'\t' read -r path row; do
    mark="${marks[$path]-}"
    if [[ -n $mark ]]; then
      row="$(printf '%-*s  \033[1;31m%s\033[0m' "$width" "$row" "$mark")"
      longest="$((${#mark} > longest ? ${#mark} : longest))"
    fi
    list+="$path"$'\t'"$row"$'\n'
  done < <(paste <(echo "$files") <(echo "$rows"))
  # Only as wide as the longest row (plus fzf's gutter).
  width="$((width + (longest > 0 ? longest + 2 : 0) + 4))"
  cols="$(stty size </dev/tty | cut -d' ' -f2)"
  margin="$((cols > width ? cols - width : 0))"
  clear
  file="$(
    printf '%s' "$list" |
      fzf --ansi --delimiter '\t' --with-nth 2 --height '~40%' --reverse \
        --margin "0,$margin,0,0" --query "$1" --select-1 |
      cut -f1
  )"
  [[ -n $file ]] || return 1
  if [[ $file != gcode/* ]]; then
    kind=cad
  else
    kind=gcode
    # Scripts name their output after themselves.
    output="tmp/$(basename "$file" .py).gcode"
  fi
}

detach() {
  setsid --fork "$@" >/dev/null 2>&1 </dev/null
}

# The programs launched from here, by name: {"orca": {"pid": 1, "started": "2"}}.
# Absolute, as Orca is launched from another directory.
PIDS="$PWD/tmp/pids.json"

# Print when process $1 started, in the kernel's ticks since boot: this tells
# it from a later process that was given the same PID.
started() {
  local stat
  stat="$(cat "/proc/$1/stat" 2>/dev/null)" || return 1
  # Count fields from after the command's name, which may hold spaces.
  stat="${stat##*) }"
  cut -d' ' -f20 <<<"$stat"
}

# Print what $PIDS holds, or an empty object if it is missing or broken.
known_pids() {
  jq --compact-output --exit-status 'objects' "$PIDS" 2>/dev/null || echo '{}'
}

# Terminate the process $1 that started at $2, failing if it is no longer running.
stop() {
  [[ -n $2 && "$(started "$1")" == "$2" ]] || return 1
  # Each launch leads its own process group, so this reaches what it started
  # too: Orca runs inside a sandbox wrapper.
  kill -TERM -- "-$1" 2>/dev/null
}

# Terminate every program launched from here, listing into $closed those that
# were still running.
close_all() {
  local name pid start
  closed=()
  while read -r name pid start; do
    if stop "$pid" "$start"; then
      closed+=("$name")
    fi
  done < <(known_pids | jq --raw-output 'to_entries[] | "\(.key) \(.value.pid) \(.value.started)"')
  rm -f "$PIDS"
}

# Run a program detached under the name $1, first terminating the one last
# launched under that name, if it is still running.
launch() {
  local name="$1" known old pid start
  shift
  known="$(known_pids)"
  old="$(jq --raw-output --arg name "$name" \
    '.[$name] // empty | "\(.pid) \(.started)"' <<<"$known")"
  if [[ -n $old ]]; then
    read -r pid start <<<"$old"
    stop "$pid" "$start" || true
  fi
  # In the background, setsid needn't fork, so $! is the program itself.
  setsid "$@" >/dev/null 2>&1 </dev/null &
  pid=$!
  start="$(started "$pid")" || start=""
  jq --arg name "$name" --argjson pid "$pid" --arg started "$start" \
    '.[$name] = {pid: $pid, started: $started, args: $ARGS.positional}' \
    --args "$@" <<<"$known" >"$PIDS.new"
  mv "$PIDS.new" "$PIDS"
}

# Succeed if the program last launched under the name $1 is still running, with
# the arguments that follow.
running() {
  local name="$1" pid start
  shift
  read -r pid start < <(known_pids | jq --raw-output --arg name "$name" \
    --args '.[$name] // empty | select(.args == $ARGS.positional)
      | "\(.pid) \(.started)"' "$@") || return 1
  [[ -n $start && "$(started "$pid")" == "$start" ]]
}

# List $file's generated projects into $projects.
find_projects() {
  shopt -s nullglob
  projects=("gen/${file%.*}-"*.3mf)
  shopt -u nullglob
}

# Pick from what $file's last generation listed, its views and objects, into
# $picked, a name to a line: one, or with --multi any number. Fails if nothing
# is listed, or picked.
pick_listed() {
  local listed="gen/${file%.py}-views.tsv"
  picked=""
  [[ -e $listed ]] || return 1
  printf '\n'
  # Each line is a kind (view or object), a name and a description; show
  # them as columns, the kind in color and the description dimmed.
  picked="$(
    awk -F '\t' '
      { kind[NR] = $1; name[NR] = $2; desc[NR] = $3 }
      length($2) > width { width = length($2) }
      END {
        for (i = 1; i <= NR; i++) {
          color = kind[i] == "view" ? "36" : "33"
          printf "%s\t\033[%sm%-6s\033[0m  %-*s  \033[2m%s\033[0m\n",
            name[i], color, kind[i], width, name[i], desc[i]
        }
      }' "$listed" |
      fzf --ansi --delimiter '\t' --with-nth 2 --height '~40%' \
        --reverse --select-1 "$@" |
      cut -f1
  )" || return 1
  [[ -n $picked ]]
}

# Describe into $fresh whether what $file generates is older than its sources,
# and say so in $state: missing, stale or fresh.
check_fresh() {
  if [[ $kind == gcode ]]; then
    check_fresh_gcode
  else
    check_fresh_model
  fi
  case "$state" in
    missing) fresh=$'\033[33mnot generated\033[0m' ;;
    stale) fresh=$'\033[33mstale: '"$changed"$' changed\033[0m' ;;
    fresh) fresh=$'\033[32mfresh\033[0m' ;;
  esac
}

# A script's sources are itself and the library it imports.
check_fresh_gcode() {
  local src
  if [[ ! -e $output ]]; then
    state=missing
    return
  fi
  for src in "$file" python/lib/*.py; do
    if [[ $src -nt $output ]]; then
      state=stale
      changed="$(basename "$src")"
      return
    fi
  done
  state=fresh
}

# A model's sources are the .py, .svg and .json files beside it, which it may
# import or read, and the shared designs in python/designs.
check_fresh_model() {
  local oldest project src dir
  find_projects
  if ((${#projects[@]} == 0)); then
    state=missing
    return
  fi
  oldest="${projects[0]}"
  for project in "${projects[@]}"; do
    if [[ $project -ot $oldest ]]; then
      oldest="$project"
    fi
  done
  dir="$(dirname "$file")"
  shopt -s nullglob
  for src in "$dir"/*.py "$dir"/*.svg "$dir"/*.json python/designs/*.py; do
    if [[ $src -nt $oldest ]]; then
      shopt -u nullglob
      state=stale
      changed="$(basename "$src")"
      return
    fi
  done
  shopt -u nullglob
  state=fresh
}

# Draw the file and its keys: below what is on screen if $keep, or on a clear one.
draw() {
  if [[ -n $keep ]]; then
    printf '\n'
  else
    clear
  fi
  keep=""
  check_fresh
  printf '\033[1m%s\033[0m\n\n' "$file"
  draw_notes
  # $below is how far the cursor ends up below the generate line.
  if [[ $kind == cad ]]; then
    draw_generate
    printf '  \033[1mG\033[0m    generate only some objects and views (tab picks more)\n'
    printf '  \033[1mo\033[0m    open a generated project in OrcaSlicer\n'
    printf '  \033[1mv\033[0m    view a generated object in FreeCAD\n'
    printf '  \033[1md\033[0m    view what the changes since HEAD do, in FreeCAD\n'
    below=8
  else
    draw_generate
    printf '  \033[1mv\033[0m    view the G-code\n'
    printf '  \033[1mh\033[0m    view the 3D preview in a browser\n'
    printf '  \033[1mu\033[0m    upload the G-code to the printer, without printing\n'
    printf '  \033[1mp\033[0m    open the printer'"'"'s page, to print from\n'
    below=8
  fi
  printf '  \033[1mc\033[0m    close the programs opened from here\n'
  printf '  \033[1mesc\033[0m  pick another file\n'
  printf '  \033[1mq\033[0m    quit\n'
  if [[ -n $status ]]; then
    printf '\n%s\n' "$status"
    below=$((below + 2))
  fi
}

# Show what $file's last generation noted to do by hand, if anything: loudly,
# as it's what a print goes wrong without.
draw_notes() {
  local notes="gen/${file%.py}-notes.txt" line
  [[ $kind == cad && -s $notes ]] || return 0
  printf '  \033[1;30;43m BY HAND, BEFORE PRINTING \033[0m\n'
  while IFS= read -r line; do
    printf '  \033[33m▌\033[0m \033[1m%s\033[0m\n' "$line"
  done <"$notes"
  printf '\n'
}

draw_generate() {
  local what="Orca projects"
  if [[ $kind == gcode ]]; then
    what="G-code"
  fi
  printf '  \033[1mg\033[0m    generate %s (%s)\033[K\n' "$what" "$fresh"
}

# Watch $file's sources and what it generates, with a line on $events for
# each change. Not a signal: one that lands mid-printf fails the write
# (EINTR), which errexit turns into a crash.
watch() {
  local dirs=("$(dirname "$file")" python/designs gen)
  if [[ $kind == gcode ]]; then
    dirs=("$(dirname "$file")" python/lib tmp)
  fi
  unwatch
  exec {events}< <(inotifywait --monitor --quiet --recursive \
    --event close_write,move,create,delete "${dirs[@]}" 2>/dev/null)
  watcher=$!
}

unwatch() {
  if [[ -n $watcher ]]; then
    kill "$watcher" 2>/dev/null || true
    exec {events}<&-
  fi
  watcher=""
}

# Wait for a key into $key, failing at the end of input, and redraw the
# generate line whenever a watched file changes in the meantime.
read_key() {
  local got
  while true; do
    got=0
    IFS= read -rsn1 -t 0.2 key || got=$?
    if ((got == 0)); then
      return 0
    elif ((got <= 128)); then
      return 1
    fi
    on_change
  done
}

# Rewrite just the generate line, if anything changed, to leave any log on
# screen alone.
on_change() {
  local was="$fresh" any=""
  while IFS= read -r -t 0.01 -u "$events" _; do any=1; done
  if [[ -z $any ]]; then
    return
  fi
  check_fresh
  if [[ $fresh != "$was" ]]; then
    printf '\033[%dA\r' "$below"
    draw_generate
    printf '\033[%dB' "$((below - 1))"
  fi
}

status=""
kind=""
output=""
state=""
changed=""
# Whether to leave what is on screen, and print the keys below it.
keep=""
closed=()
watcher=""
events=""
trap unwatch EXIT

pick "$*" || exit 0
watch

while true; do
  draw
  read_key || exit 0
  status=""
  case "$kind:$key" in
    cad:g | gcode:g)
      printf '\nGenerating...\n'
      # Leave the log on screen, to read.
      keep=1
      # A build123d project by way of build.generate, as `just generate`
      # runs it; a G-code script as itself.
      run=("$file")
      if [[ $kind == cad ]]; then run=(python -m build.generate "$file"); fi
      if ! uv --project python run "${run[@]}" 2>&1; then
        status="Generation failed."
      fi
      ;;
    cad:G)
      # Just those, leaving the rest of what's generated as it is, stale or
      # not: the list is the last generation's.
      if [[ ! -e gen/${file%.py}-views.tsv ]]; then
        status="Nothing generated for $file yet; press g."
        continue
      fi
      pick_listed --multi || continue
      mapfile -t names <<<"$picked"
      printf '\nGenerating %s...\n' "${names[*]}"
      keep=1
      if ! uv --project python run python -m build.generate "$file" "${names[@]}" 2>&1; then
        status="Generation failed."
      fi
      ;;
    gcode:v)
      if [[ $state == missing ]]; then
        status="Nothing generated for $file yet; press g."
        continue
      fi
      launch gcodeviewer prusa-gcodeviewer "$output"
      status="Opened $output in PrusaSlicer's G-code viewer."
      ;;
    gcode:h)
      if [[ ! -e ${output%.gcode}.html ]]; then
        status="No 3D preview for $file; press g, though not every script writes one."
        continue
      fi
      detach xdg-open "${output%.gcode}.html"
      status="Opened ${output%.gcode}.html in a browser."
      ;;
    gcode:u)
      # Never upload G-code that isn't what the script now says.
      if [[ $state != fresh ]]; then
        status="$output is not up to date; press g first."
        continue
      fi
      printf '\nUploading %s to %s...\n' "$output" "$PRINTER"
      if curl --silent --show-error --fail --max-time 60 --output /dev/null \
        --form "file=@$output" "http://$PRINTER/server/files/upload"; then
        status="Uploaded $(basename "$output"); print it from http://$PRINTER (press p)."
      else
        status="Upload failed."
        keep=1
      fi
      ;;
    gcode:p)
      detach xdg-open "http://$PRINTER"
      status="Opened http://$PRINTER in a browser."
      ;;
    cad:o)
      find_projects
      if ((${#projects[@]} == 0)); then
        status="Nothing generated for $file yet; press g."
        continue
      fi
      printf '\n'
      project="$(
        printf '%s\n' "${projects[@]}" |
          fzf --delimiter / --with-nth -1 --height '~40%' --reverse --select-1
      )" || continue
      # Orca writes a result.json into its working directory.
      (cd "${TMPDIR:-/tmp}" && launch orca orca-slicer "$OLDPWD/$project")
      status="Opened $project in OrcaSlicer."
      ;;
    cad:v)
      # Generating writes each object and view as a STEP file, and lists them.
      if [[ ! -e gen/${file%.py}-views.tsv ]]; then
        status="Nothing generated for $file yet; press g."
        continue
      fi
      pick_listed || continue
      object="$picked"
      view="gen/${file%.py}-$object.step"
      # FreeCAD reloads what it has open when it changes (see nix/fit.FCMacro).
      if running freecad freecad "$view" nix/fit.FCMacro; then
        status="$view is already open in FreeCAD, which reloads it when it's generated."
      else
        launch freecad freecad "$view" nix/fit.FCMacro
        status="Opened $view in FreeCAD, which reloads it when it's generated."
      fi
      if [[ $state == stale ]]; then
        status+=" It's stale; press g to bring it up to date."
      fi
      ;;
    cad:d)
      printf '\nDiffing against HEAD...\n'
      # Leave the log on screen, to read.
      keep=1
      # It writes no diff if no piece differs.
      diffed=tmp/diff/diff.step
      if ! uv --project python run python/diff.py "$file" --no-open 2>&1; then
        status="Diff failed."
      elif [[ ! -e $diffed ]]; then
        status="No piece of $file differs from HEAD."
      else
        if running diff freecad "$diffed" nix/fit.FCMacro; then
          status="Diff updated in the open FreeCAD."
        else
          launch diff freecad "$diffed" nix/fit.FCMacro
          status="Opened $diffed in FreeCAD."
        fi
      fi
      ;;
    *:c)
      close_all
      if ((${#closed[@]} == 0)); then
        status="Nothing open to close."
      else
        status="Closed ${closed[*]}."
      fi
      ;;
    *:$'\e')
      # Arrow and function keys send more after the escape; ignore those.
      rest=""
      IFS= read -rsn8 -t 0.05 rest || true
      if [[ -z $rest ]]; then
        pick "" || exit 0
        watch
      fi
      ;;
    *:q)
      clear
      exit 0
      ;;
  esac
done
