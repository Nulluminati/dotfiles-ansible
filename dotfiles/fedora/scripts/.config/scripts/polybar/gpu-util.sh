#!/bin/bash
# Intel iGPU utilization for polybar
# Uses intel_gpu_top with CSV output

if ! command -v intel_gpu_top &> /dev/null; then
    echo "N/A"
    exit 0
fi

# intel_gpu_top needs cap_perfmon capability to run without root
# Run once: sudo setcap cap_perfmon=ep /usr/bin/intel_gpu_top

# Sample for one iteration with CSV output
# First line is header, lines 2+ are data
# Skip first data line (often 0), use second data line for actual reading
# CSV columns: Freq MHz req, Freq MHz act, IRQ /s, RC6 %, RCS %, ...
# RCS % (column 5) is Render Command Streamer = Render/3D utilization
CSV_OUTPUT=$(intel_gpu_top -c -s 500 2>/dev/null | head -3 | tail -1)

if [ -z "$CSV_OUTPUT" ]; then
    echo "N/A"
    exit 0
fi

# Extract RCS % (5th column) - this is the render/3D engine utilization
# Round to nearest integer
RENDER_BUSY=$(echo "$CSV_OUTPUT" | cut -d',' -f5 | awk '{printf("%.0f", $1)}')

if [ -n "$RENDER_BUSY" ] && [ "$RENDER_BUSY" != "" ]; then
    echo "${RENDER_BUSY}%"
else
    echo "N/A"
fi
