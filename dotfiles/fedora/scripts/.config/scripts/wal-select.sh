#!/usr/bin/env bash
# Rofi-based pywal preset selector with image previews
# Each preset applies both a wallpaper AND a theme together

PRESETS_FILE="$HOME/.config/wal/presets.conf"
CACHE_ROOT="$HOME/.config/wal/cache/thumbs"

# Check for ffmpeg/ffprobe
if ! command -v ffmpeg &>/dev/null || ! command -v ffprobe &>/dev/null; then
    echo "Error: ffmpeg and ffprobe are required for thumbnail generation"
    echo "Install with: sudo dnf install ffmpeg" 2>/dev/null || echo "Install with: sudo apt install ffmpeg"
    exit 1
fi

# Create cache directory if it doesn't exist
mkdir -p "$CACHE_ROOT"

# Check if presets file exists
if [[ ! -f "$PRESETS_FILE" ]]; then
    echo "Error: Presets file not found at $PRESETS_FILE"
    echo "Create it with format: Name|/path/to/wallpaper|theme-name"
    exit 1
fi

# Generate a 600x600 thumbnail for an image
# Arguments: $1 = input path, $2 = output path
function cacheImg {
    local resolution
    local width_
    local height_

    resolution=$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 "$1" 2>&1)
    width_=$(echo "${resolution}" | awk -F',' '{print $1}')
    height_=$(echo "${resolution}" | awk -F',' '{print $2}')

    # Skip if we couldn't get resolution
    if [[ -z "$width_" || -z "$height_" ]]; then
        >&2 echo "Warning: Could not get resolution for $1"
        return 1
    fi

    if [[ "${width_}" -lt "${height_}" ]]; then
        # Portrait: scale width to 600, then center-crop
        ffmpeg -i "$1" -loglevel warning -vf "scale=600:-1, crop=600:600:0:(iw-600)/2" "$2" -y
    else
        # Landscape: scale height to 600, then center-crop
        ffmpeg -i "$1" -loglevel warning -vf "scale=-1:600, crop=600:600:(iw-600)/2:0" "$2" -y
    fi
}

# Extract filename without extension
function getFileName {
    echo "$1" | xargs basename | awk -F'.' '{print $1}'
}

# Build list of preset names and store data for lookup
declare -A WALLPAPERS
declare -A THEMES
declare -A THUMBNAILS
PRESETS_LIST=""

while IFS='|' read -r name wallpaper theme; do
    # Skip empty lines and comments
    [[ -z "$name" || "$name" =~ ^#.* ]] && continue

    # Expand ~ in wallpaper path
    wallpaper="${wallpaper/#\~/$HOME}"

    # Skip if wallpaper doesn't exist
    [[ ! -f "$wallpaper" ]] && continue

    WALLPAPERS["$name"]="$wallpaper"
    THEMES["$name"]="$theme"

    # Generate thumbnail cache path
    cache_name=$(getFileName "$wallpaper").png
    cache_path="$CACHE_ROOT/$cache_name"

    # Generate thumbnail if it doesn't exist
    if [[ ! -f "$cache_path" ]]; then
        >&2 echo "Generating thumbnail for: $name"
        if cacheImg "$wallpaper" "$cache_path"; then
            >&2 echo "  ✓ Thumbnail created: $cache_path"
        else
            >&2 echo "  ✗ Failed to create thumbnail"
        fi
    fi

    THUMBNAILS["$name"]="$cache_path"
    PRESETS_LIST="${PRESETS_LIST}${name}"$'\n'
done < "$PRESETS_FILE"

# Build rofi input with icon syntax using temp file (command substitution strips null bytes)
TEMP_ROFI=$(mktemp)
printf '%s\n' "${!WALLPAPERS[@]}" | sort | while IFS= read -r name; do
    printf "%s\0icon\x1f%s\n" "$name" "${THUMBNAILS[$name]}" >> "$TEMP_ROFI"
done

# Get selection using rofi with thumbnails - horizontal layout with large icons
selection=$(cat "$TEMP_ROFI" | rofi -dmenu -i -p "󰸉 Theme:" \
    -no-custom \
    -mesg "Select a pywal preset" \
    -theme-str "listview { columns: 1; lines: 6; }" \
    -theme-str "element-icon { size: 80px; }" \
    -theme-str "element { padding: 8px; spacing: 15px; }" \
    -theme-str "window { width: 500px; }")
rm -f "$TEMP_ROFI"

if [[ -z "$selection" ]]; then
    exit 0
fi

# Get wallpaper and theme from selection
wallpaper="${WALLPAPERS[$selection]}"
theme="${THEMES[$selection]}"

# Validate wallpaper exists
if [[ ! -f "$wallpaper" ]]; then
    notify-send "Wal Error" "Wallpaper not found: $wallpaper" -i dialog-error
    exit 1
fi

# Apply the preset (feh for wallpaper, wal for theme colors)
# Use -n to skip wal's wallpaper setting, then use feh directly
wal -n --theme "$theme" -o ~/.config/wal/after_wal.sh
feh --bg-fill "$wallpaper"

# Optional: Notify user
if command -v notify-send &>/dev/null; then
    notify-send "Pywal Theme Applied" "Switched to: $selection" -i preferences-desktop-theme
fi
