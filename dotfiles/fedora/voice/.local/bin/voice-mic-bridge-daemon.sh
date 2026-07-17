#!/usr/bin/env bash
# voice-mic-bridge-daemon.sh — NoMachine mic → pi_voice_mic, no sidetone.
#
# Architecture: directly pw-links the NoMachine mic stream's output ports to
# pi_mic_sink's input ports (bypassing pactl move-sink-input, which sets
# stale target metadata that misdirects other audio streams to pi_mic_sink).
# The bridge monitors pi_mic_sink → pi_voice_mic source.
#
# pi_mic_sink has priority.session=-10000 so WirePlumber never auto-connects
# normal audio (pw-play, peon) to it — they always go to nx_voice_out.
set -u

MIC_SINK_NAME="pi_mic_sink"
SOURCE_NAME="pi_voice_mic"
CAPTURE_NAME="pi_voice_cap"
POLL_INTERVAL=5
LOG_TAG="[voice-bridge]"

log() { echo "$LOG_TAG $*" >&2; }

mic_linked=false

ensure_mic_sink() {
  if pw-dump 2>/dev/null | node -e "
    const d=JSON.parse(require('fs').readFileSync(0,'utf8'));
    process.exit(d.some(o=>o.info?.props?.['node.name']==='pi_mic_sink')?0:1);
  " 2>/dev/null; then return 0; fi
  log "creating mic-capture sink: $MIC_SINK_NAME"
  pw-cli create-node adapter \
    factory.name=support.null-audio-sink \
    media.class="Audio/Sink" \
    node.name="$MIC_SINK_NAME" \
    node.description="Pi Mic Capture" \
    audio.position="[FL,FR]" \
    object.linger=1 \
    monitor.channel-volumes=1 \
    priority.session=-10000 \
    2>/dev/null
  log "mic-capture sink created"
}

# Directly link the NoMachine mic stream's output ports to pi_mic_sink's
# input ports. Bypasses pactl move-sink-input entirely (no target metadata).
link_mic_to_sink() {
  if $mic_linked; then return; fi

  # Find the NoMachine Stream/Output adapter node (has output ports)
  local mic_node
  mic_node=$(pw-dump 2>/dev/null | node -e "
    const d=JSON.parse(require('fs').readFileSync(0,'utf8'));
    for(const o of d){
      const p=o.info?.props||{};
      if(p['media.class']==='Stream/Output/Audio' && /nomachine/i.test(p['node.name']||'')){
        // Check it has output ports (the adapter, not the raw client)
        const hasPorts=d.some(x=>x.type==='PipeWire:Interface:Port' && String(x.info?.props?.['node.id'])===String(o.id) && x.info?.props?.['port.direction']==='out');
        if(hasPorts) { console.log(o.id); break; }
      }
    }
  " 2>/dev/null)

  if [ -z "$mic_node" ]; then return; fi

  # Find mic output ports (FL, FR)
  local mic_fl mic_fr
  mic_fl=$(pw-dump 2>/dev/null | node -e "
    const d=JSON.parse(require('fs').readFileSync(0,'utf8'));
    for(const o of d){
      if(o.type!=='PipeWire:Interface:Port') continue;
      const p=o.info?.props||{};
      if(String(p['node.id'])==='$mic_node' && p['port.direction']==='out' && (p['port.name']||'').includes('FL')){console.log(o.id);break;}
    }
  " 2>/dev/null)
  mic_fr=$(pw-dump 2>/dev/null | node -e "
    const d=JSON.parse(require('fs').readFileSync(0,'utf8'));
    for(const o of d){
      if(o.type!=='PipeWire:Interface:Port') continue;
      const p=o.info?.props||{};
      if(String(p['node.id'])==='$mic_node' && p['port.direction']==='out' && (p['port.name']||'').includes('FR')){console.log(o.id);break;}
    }
  " 2>/dev/null)

  # Find pi_mic_sink input ports (playback_FL, playback_FR)
  local sink_fl sink_fr
  sink_fl=$(pw-dump 2>/dev/null | node -e "
    const d=JSON.parse(require('fs').readFileSync(0,'utf8'));
    for(const o of d){
      if(o.type!=='PipeWire:Interface:Port') continue;
      const p=o.info?.props||{};
      const n=d.find(x=>x.id===Number(p['node.id']));
      if(n?.info?.props?.['node.name']==='$MIC_SINK_NAME' && p['port.direction']==='in' && (p['port.name']||'').includes('FL')){console.log(o.id);break;}
    }
  " 2>/dev/null)
  sink_fr=$(pw-dump 2>/dev/null | node -e "
    const d=JSON.parse(require('fs').readFileSync(0,'utf8'));
    for(const o of d){
      if(o.type!=='PipeWire:Interface:Port') continue;
      const p=o.info?.props||{};
      const n=d.find(x=>x.id===Number(p['node.id']));
      if(n?.info?.props?.['node.name']==='$MIC_SINK_NAME' && p['port.direction']==='in' && (p['port.name']||'').includes('FR')){console.log(o.id);break;}
    }
  " 2>/dev/null)

  if [ -z "$mic_fl" ] || [ -z "$sink_fl" ]; then
    log "ERROR: could not find mic output or sink input ports"
    return
  fi

  # Remove existing links from mic to nx_voice_out (if any)
  for link_id in $(pw-dump 2>/dev/null | node -e "
    const d=JSON.parse(require('fs').readFileSync(0,'utf8'));
    const links=d.filter(o=>o.type==='PipeWire:Interface:Link');
    for(const l of links){
      if(l.info?.['output-node-id']===$mic_node) console.log(l.id);
    }
  " 2>/dev/null); do
    pw-cli destroy "$link_id" 2>/dev/null
  done

  # Link mic output → pi_mic_sink input
  log "linking mic($mic_node) -> $MIC_SINK_NAME (FL:$mic_fl→$sink_fl, FR:$mic_fr→$sink_fr)"
  pw-link "$mic_fl" "$sink_fl" 2>/dev/null
  [ -n "$mic_fr" ] && [ -n "$sink_fr" ] && pw-link "$mic_fr" "$sink_fr" 2>/dev/null
  mic_linked=true
  log "mic linked to $MIC_SINK_NAME"
}

# Detect if mic stream disappeared (NoMachine reconnect)
check_mic_gone() {
  local found
  found=$(pw-dump 2>/dev/null | node -e "
    const d=JSON.parse(require('fs').readFileSync(0,'utf8'));
    let found=d.some(o=>{
      const p=o.info?.props||{};
      return p['media.class']==='Stream/Output/Audio' && /nomachine/i.test(p['node.name']||'');
    });
    console.log(found?'yes':'no');
  " 2>/dev/null)
  if [ "$found" = "no" ] && $mic_linked; then
    log "mic stream disappeared — will re-link on next appearance"
    mic_linked=false
  fi
}

setup_source_bridge() {
  for pid in $(pgrep -x pw-loopback 2>/dev/null); do
    if cat /proc/$pid/cmdline 2>/dev/null | tr '\0' ' ' | grep -q "pi_voice"; then
      kill "$pid" 2>/dev/null
    fi
  done

  log "creating Audio/Source: $SOURCE_NAME"
  pw-loopback \
    --capture-props="media.class=Stream/Input/Audio node.name=$CAPTURE_NAME node.autoconnect=false" \
    --playback-props="media.class=Audio/Source node.name=$SOURCE_NAME node.description='Pi Voice Mic' audio.position=[mono]" \
    >/dev/null 2>&1 &
  local lb_pid=$!

  local cap_node=""
  for _ in $(seq 1 8); do
    cap_node=$(pw-dump 2>/dev/null | node -e "
      const d=JSON.parse(require('fs').readFileSync(0,'utf8'));
      for(const o of d){if(o.info?.props?.['node.name']==='$CAPTURE_NAME'){console.log(o.id);break;}}
    " 2>/dev/null)
    [ -n "$cap_node" ] && break
    sleep 0.5
  done

  if [ -z "$cap_node" ]; then
    log "ERROR: capture node did not appear"
    kill "$lb_pid" 2>/dev/null
    return 1
  fi

  local cap_in
  cap_in=$(pw-dump 2>/dev/null | node -e "
    const d=JSON.parse(require('fs').readFileSync(0,'utf8'));
    for(const o of d){
      if(o.type!=='PipeWire:Interface:Port') continue;
      const p=o.info?.props||{};
      if(String(p['node.id'])==='$cap_node' && p['port.direction']==='in' && (p['port.name']||'').includes('FL')){console.log(o.id);break;}
    }
  " 2>/dev/null)

  local mon_port
  mon_port=$(pw-dump 2>/dev/null | node -e "
    const d=JSON.parse(require('fs').readFileSync(0,'utf8'));
    for(const o of d){
      if(o.type!=='PipeWire:Interface:Port') continue;
      const p=o.info?.props||{};
      const n=d.find(x=>x.id===Number(p['node.id']));
      if(n?.info?.props?.['node.name']==='$MIC_SINK_NAME' && p['port.name']==='monitor_FL'){
        console.log(o.id);break;
      }
    }
  " 2>/dev/null)

  if [ -z "$mon_port" ] || [ -z "$cap_in" ]; then
    log "ERROR: monitor_FL ($mon_port) or capture input ($cap_in) not found"
    kill "$lb_pid" 2>/dev/null
    return 1
  fi

  log "linking monitor_FL($mon_port) -> capture input_FL($cap_in)"
  pw-link "$mon_port" "$cap_in" 2>/dev/null || true
  log "bridge is UP (pid $lb_pid, source $SOURCE_NAME)"
  echo "$lb_pid"
}

# --- Main loop ---
log "daemon started (no-sidetone, direct-link mode)"

while true; do
  ensure_mic_sink
  link_mic_to_sink
  check_mic_gone

  bridge_alive=false
  for pid in $(pgrep -x pw-loopback 2>/dev/null); do
    if cat /proc/$pid/cmdline 2>/dev/null | tr '\0' ' ' | grep -q "pi_voice_mic"; then
      bridge_alive=true
      break
    fi
  done

  if [ "$bridge_alive" = false ]; then
    setup_source_bridge >/dev/null 2>&1
  fi

  sleep "$POLL_INTERVAL"
done