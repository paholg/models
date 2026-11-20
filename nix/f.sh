# Pick a design with fzf, then act on it with single keys. A design is a .scad
# file or a build123d project (a .py file among them), which become Orca
# projects, or a script in gcode/, which writes G-code.
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

# Pick a design into $file and its $kind (scad, cad or gcode), starting from the query $1.
pick() {
  local files rows list path row mark longest width cols margin
  files="$({
    fd --extension scad
    # A project is told from any other script by what it imports.
    fd --extension py --exclude python --exclude gcode \
      --exec-batch grep --files-with-matches '^from build\.cad import' |
      sed 's|^\./||' || true
    fd --extension py . gcode
  } | sort)"
  # Show path components as aligned columns, without the suffix;
  # the real path rides along in a hidden first field.
  rows="$(echo "$files" | sed -E 's/\.(scad|py)$//' | column -t -s/ -o '  ')"
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
  if [[ $file == *.scad ]]; then
    kind=scad
  elif [[ $file != gcode/* ]]; then
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

# The programs launched from here, by name: {"openscad": {"pid": 1, "started": "2"}}.
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
    '.[$name] = {pid: $pid, started: $started}' <<<"$known" >"$PIDS.new"
  mv "$PIDS.new" "$PIDS"
}

# List $file's generated projects into $projects.
find_projects() {
  shopt -s nullglob
  projects=("gen/${file%.*}-"*.3mf)
  shopt -u nullglob
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

# A model's sources are the .scad, .py and .svg files beside it, which it may
# include or import, and the shared designs in python/designs.
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
  for src in "$dir"/*.scad "$dir"/*.py "$dir"/*.svg python/designs/*.py; do
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
  # $below is how far the cursor ends up below the generate line.
  if [[ $kind == scad ]]; then
    printf '  \033[1ms\033[0m    open in OpenSCAD\n'
    draw_generate
    printf '  \033[1mo\033[0m    open a generated project in OrcaSlicer\n'
    below=5
  elif [[ $kind == cad ]]; then
    draw_generate
    printf '  \033[1mo\033[0m    open a generated project in OrcaSlicer\n'
    printf '  \033[1mv\033[0m    view an object in FreeCAD\n'
    below=6
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

draw_generate() {
  local what="Orca projects"
  if [[ $kind == gcode ]]; then
    what="G-code"
  fi
  printf '  \033[1mg\033[0m    generate %s (%s)\033[K\n' "$what" "$fresh"
}

# Watch $file's sources and what it generates, signalling this shell when one changes.
watch() {
  local dirs=("$(dirname "$file")" python/designs gen)
  if [[ $kind == gcode ]]; then
    dirs=("$(dirname "$file")" python/lib tmp)
  fi
  unwatch
  inotifywait --monitor --quiet --recursive \
    --event close_write,move,create,delete "${dirs[@]}" \
    > >(while read -r _; do kill -USR1 $$ 2>/dev/null || exit; done) 2>/dev/null &
  watcher=$!
}

unwatch() {
  if [[ -n $watcher ]]; then
    kill "$watcher" 2>/dev/null || true
  fi
  watcher=""
}

# Bash runs this in the middle of the `read` that waits for a key.
# Rewrite just the generate line, to leave any log on screen alone.
on_change() {
  local was="$fresh"
  if [[ -z $waiting ]]; then
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
waiting=""
watcher=""
trap on_change USR1
trap unwatch EXIT

pick "$*" || exit 0
watch

while true; do
  draw
  waiting=1
  IFS= read -rsn1 key || exit 0
  waiting=""
  status=""
  case "$kind:$key" in
    scad:s)
      launch openscad openscad "$file"
      status="Opened $file in OpenSCAD."
      ;;
    scad:g)
      printf '\nGenerating...\n'
      # Leave the log on screen only if there is a failure in it to read.
      if ! uv --project python run python/generate.py "$file" 2>&1; then
        status="Generation failed."
        keep=1
      fi
      ;;
    cad:g | gcode:g)
      printf '\nGenerating...\n'
      # Leave the log on screen only if there is a failure in it to read.
      if ! uv --project python run "$file" 2>&1; then
        status="Generation failed."
        keep=1
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
    scad:o | cad:o)
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
      objects="$(uv --project python run "$file" --objects)" || {
        status="Couldn't list the objects of $file."
        keep=1
        continue
      }
      printf '\n'
      # Each line is a kind (view or object), a name and a description; show
      # them as columns, the kind in color and the description dimmed.
      object="$(
        awk -F '\t' '
          { kind[NR] = $1; name[NR] = $2; desc[NR] = $3 }
          length($2) > width { width = length($2) }
          END {
            for (i = 1; i <= NR; i++) {
              color = kind[i] == "view" ? "36" : "33"
              printf "%s\t\033[%sm%-6s\033[0m  %-*s  \033[2m%s\033[0m\n",
                name[i], color, kind[i], width, name[i], desc[i]
            }
          }' <<<"$objects" |
          fzf --ansi --delimiter '\t' --with-nth 2 --height '~40%' \
            --reverse --select-1 |
          cut -f1
      )" || continue
      [[ -n $object ]] || continue
      printf '\nExporting...\n'
      if ! uv --project python run "$file" --view "$object" 2>&1; then
        status="Export failed."
        keep=1
        continue
      fi
      view="tmp/view/$(basename "$file" .py)-$object.step"
      launch freecad freecad "$view"
      status="Opened $view in FreeCAD."
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
