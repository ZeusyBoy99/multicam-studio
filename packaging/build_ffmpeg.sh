#!/bin/sh
set -eu
WORK=${1:?Usage: build_ffmpeg.sh WORK_DIRECTORY}
ARCH=${2:-$(uname -m)}
case "$ARCH" in arm64) HOST=aarch64-apple-darwin ;; x86_64) HOST=x86_64-apple-darwin ;; *) exit 2 ;; esac
PREFIX="$WORK/ffmpeg-$ARCH"
SOURCES="$WORK/sources"
mkdir -p "$SOURCES" "$PREFIX"
export MACOSX_DEPLOYMENT_TARGET=13.0
X264_COMMIT=b35605ace3ddf7c1a5d67a2eb553f034aef41d55
if [ ! -f "$SOURCES/ffmpeg-9.0.1.tar.xz" ]; then
  curl --fail --location --retry 3 https://ffmpeg.org/releases/ffmpeg-9.0.1.tar.xz -o "$SOURCES/ffmpeg-9.0.1.tar.xz"
fi
printf '%s  %s\n' cf38e0e28c7e5605942c4a77755349b0145804a397af37eb1fb4c77cb237f635 "$SOURCES/ffmpeg-9.0.1.tar.xz" | shasum -a 256 -c -
if [ ! -f "$SOURCES/x264-$X264_COMMIT.tar.bz2" ]; then
  curl --fail --location --retry 3 "https://code.videolan.org/videolan/x264/-/archive/$X264_COMMIT/x264-$X264_COMMIT.tar.bz2" -o "$SOURCES/x264-$X264_COMMIT.tar.bz2"
fi
printf '%s  %s\n' 6eeb82934e69fd51e043bd8c5b0d152839638d1ce7aa4eea65a3fedcf83ff224 "$SOURCES/x264-$X264_COMMIT.tar.bz2" | shasum -a 256 -c -
if [ ! -f "$PREFIX/lib/libx264.a" ]; then
  mkdir -p "$WORK/x264-$ARCH"
  tar -xjf "$SOURCES/x264-$X264_COMMIT.tar.bz2" -C "$WORK/x264-$ARCH" --strip-components=1
  cd "$WORK/x264-$ARCH"
  ./configure --prefix="$PREFIX" --host="$HOST" --enable-static --enable-pic --disable-cli --disable-opencl --extra-cflags="-arch $ARCH -mmacosx-version-min=13.0" --extra-ldflags="-arch $ARCH -mmacosx-version-min=13.0"
  make -j4
  make install
fi
mkdir -p "$WORK/ffmpeg-build-$ARCH"
tar -xJf "$SOURCES/ffmpeg-9.0.1.tar.xz" -C "$WORK/ffmpeg-build-$ARCH" --strip-components=1
cd "$WORK/ffmpeg-build-$ARCH"
export PKG_CONFIG_PATH="$PREFIX/lib/pkgconfig"
./configure --prefix="$PREFIX" --arch="$ARCH" --target-os=darwin --cc=clang \
  --extra-cflags="-arch $ARCH -mmacosx-version-min=13.0 -I$PREFIX/include" \
  --extra-ldflags="-arch $ARCH -mmacosx-version-min=13.0 -L$PREFIX/lib" \
  --disable-autodetect --disable-shared --enable-static --disable-debug --disable-doc --disable-ffplay \
  --disable-everything --enable-gpl --enable-libx264 --enable-pthreads \
  --enable-protocol=file,pipe \
  --enable-demuxers --enable-decoders --enable-parsers --enable-filters --enable-bsfs \
  --enable-muxer=mp4,mov,image2,image2pipe,wav,pcm_f32le,pcm_s16le,rawvideo,null,adts \
  --enable-decoder=wrapped_avframe,rawvideo,h264,hevc,prores,mpeg4,mjpeg,png,vp9,aac,alac,pcm_s16le,pcm_s24le,pcm_s32le,pcm_f32le,pcm_f64le,pcm_s16be,pcm_s24be,pcm_s32be,mp3,flac,opus \
  --enable-parser=h264,hevc,mpeg4video,mjpeg,vp9,aac,mpegaudio,flac,opus \
  --enable-encoder=wrapped_avframe,libx264,aac,pcm_f32le,pcm_s16le,rawvideo,mjpeg,png \
  --enable-filter=scale,crop,pad,setsar,setpts,asetpts,aresample,highpass,lowpass,atrim,trim,fps,tpad,format,color,hue,colorbalance,eq,vignette,fade,afade,testsrc,testsrc2,sine,aevalsrc,anullsrc,anull,null,select,aselect,showinfo,ashowinfo \
  --enable-indev=lavfi
make -j4
make install
(cd "$SOURCES" && shasum -a 256 ffmpeg-9.0.1.tar.xz "x264-$X264_COMMIT.tar.bz2" > SHA256SUMS)
"$PREFIX/bin/ffmpeg" -version
