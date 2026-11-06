#!/usr/bin/env bash
set -euo pipefail
scene="$1"
preview="${2:-0}"
FONT=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf
mkdir -p final
ls frames | head -3
n=$(ls frames/frame_*.jpg | wc -l)
echo "frames: $n"

if [ "$preview" = "1" ]; then
  # 2x2 contact sheet of the 4 preview frames
  ffmpeg -y -pattern_type glob -i 'frames/frame_*.jpg' -filter_complex "tile=2x2" -frames:v 1 -update 1 "final/${scene}_sheet.png"
  exit 0
fi

ffmpeg -y -framerate 24 -i frames/frame_%04d.jpg -c:v libx264 -crf 14 -preset medium -pix_fmt yuv420p "final/${scene}_clean.mp4"

if [ "$scene" = "assassin" ]; then
cat > vf.txt <<EOF
eq=contrast=1.06:saturation=1.18,vignette=PI/4.5,noise=alls=5:allf=t,drawbox=x=0:y=0:w=iw:h=ih*0.085:color=black:t=fill,drawbox=x=0:y=ih*0.915:w=iw:h=ih*0.085:color=black:t=fill,drawtext=fontfile=${FONT}:text='MEMORY SYNCHRONIZED':fontsize=30:fontcolor=white:alpha='if(lt(t,1.2),0,if(lt(t,2.2),t-1.2,if(lt(t,5.5),1,if(lt(t,6.5),6.5-t,0))))':x=(w-text_w)/2:y=h*0.92-text_h/2:box=0,fade=t=in:st=0:d=0.7,fade=t=out:st=9.3:d=0.7
EOF
else
cat > vf.txt <<EOF
eq=contrast=1.04:saturation=1.1,vignette=PI/6,drawtext=fontfile=${FONT}:text='CHAPTER ONE':fontsize=22:fontcolor=white@0.85:alpha='if(lt(t,0.8),0,if(lt(t,1.6),(t-0.8)/0.8,1))':x=56:y=h-120,drawtext=fontfile=${FONT}:text='A small island  a long journey':fontsize=44:fontcolor=white:alpha='if(lt(t,1.0),0,if(lt(t,1.8),(t-1.0)/0.8,1))':x=56:y=h-92,fade=t=in:st=0:d=0.6,fade=t=out:st=9.4:d=0.6
EOF
fi

ffmpeg -y -framerate 24 -i frames/frame_%04d.jpg -filter_script:v vf.txt -c:v libx264 -crf 15 -preset medium -pix_fmt yuv420p "final/${scene}.mp4"
ls -la final
