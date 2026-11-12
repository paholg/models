# Pick a .scad file with fzf, then act on it with single keys.
cd "$(git rev-parse --show-toplevel)" || exit

# Pick a .scad file into $file, starting from the query $1.
pick() {
  local files rows width cols margin
  files="$(fd --extension scad | sort)"
  # Show path components as aligned columns, without the suffix;
  # the real path rides along in a hidden first field.
  rows="$(echo "$files" | sed 's/\.scad$//' | column -t -s/ -o '  ')"
  # Only as wide as the longest row (plus fzf's gutter).
  width="$(($(echo "$rows" | wc -L) + 4))"
  cols="$(stty size </dev/tty | cut -d' ' -f2)"
  margin="$((cols > width ? cols - width : 0))"
  clear
  file="$(
    paste <(echo "$files") <(echo "$rows") |
      fzf --delimiter '\t' --with-nth 2 --height '~40%' --reverse \
        --margin "0,$margin,0,0" --query "$1" --select-1 |
      cut -f1
  )"
  [[ -n $file ]]
}

detach() {
  setsid --fork "$@" >/dev/null 2>&1 </dev/null
}

# List $file's generated projects into $projects.
find_projects() {
  shopt -s nullglob
  projects=("gen/${file%.scad}-"*.3mf)
  shopt -u nullglob
}

# Describe into $fresh whether $file's projects are older than its sources:
# the .scad and .svg files beside it, which it may include or import.
check_fresh() {
  local oldest project src dir
  find_projects
  if ((${#projects[@]} == 0)); then
    fresh=$'\033[33mnot generated\033[0m'
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
  for src in "$dir"/*.scad "$dir"/*.svg; do
    if [[ $src -nt $oldest ]]; then
      shopt -u nullglob
      fresh=$'\033[33mstale: '"$(basename "$src")"$' changed\033[0m'
      return
    fi
  done
  shopt -u nullglob
  fresh=$'\033[32mfresh\033[0m'
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
  printf '  \033[1ms\033[0m    open in OpenSCAD\n'
  draw_generate
  printf '  \033[1mo\033[0m    open a generated project in OrcaSlicer\n'
  printf '  \033[1mesc\033[0m  pick another file\n'
  printf '  \033[1mq\033[0m    quit\n'
  # How far the cursor ends up below the generate line.
  below=4
  if [[ -n $status ]]; then
    printf '\n%s\n' "$status"
    below=6
  fi
}

draw_generate() {
  printf '  \033[1mg\033[0m    generate Orca projects (%s)\033[K\n' "$fresh"
}

# Watch $file's sources and projects, signalling this shell when one changes.
watch() {
  unwatch
  inotifywait --monitor --quiet --recursive \
    --event close_write,move,create,delete "$(dirname "$file")" gen \
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
# Whether to leave what is on screen, and print the keys below it.
keep=""
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
  case "$key" in
    s)
      detach openscad "$file"
      status="Opened $file in OpenSCAD."
      ;;
    g)
      printf '\nGenerating...\n'
      uv --project python run python/generate.py "$file" 2>&1 || status="Generation failed."
      keep=1
      ;;
    o)
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
      (cd "${TMPDIR:-/tmp}" && detach orca-slicer "$OLDPWD/$project")
      status="Opened $project in OrcaSlicer."
      ;;
    $'\e')
      # Arrow and function keys send more after the escape; ignore those.
      rest=""
      IFS= read -rsn8 -t 0.05 rest || true
      if [[ -z $rest ]]; then
        pick "" || exit 0
        watch
      fi
      ;;
    q)
      clear
      exit 0
      ;;
  esac
done
