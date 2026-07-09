import os
import subprocess

def merge_audio_with_video(video_path, audio_path, orig_volume=0.3, dub_volume=1.0):
    """
    orig_volume: 0.0 - 1.0 (volume tiếng gốc)
    dub_volume: 0.0 - 1.0 (volume lồng tiếng)
    """
    print("Đang xử lý ghép âm thanh vào khung hình video...")
    
    base_dir = os.path.dirname(os.path.dirname(__file__))
    temp_dir = os.path.join(base_dir, 'temp')
    output_path = os.path.join(base_dir, 'final_dubbed_video.mp4')
    
    # Cách 1: Sử dụng FFmpeg (Subprocess) -> Rất nhanh do không encode lại video
    try:
        command = [
            'ffmpeg', '-i', video_path, '-i', audio_path,
            '-filter_complex',
            f'[0:a:0]volume={orig_volume}[orig];[1:a:0]volume={dub_volume}[dub];[orig][dub]amix=inputs=2:duration=first:dropout_transition=0[out]',
            '-c:v', 'copy',
            '-map', '0:v:0',
            '-map', '[out]',
            '-c:a', 'aac',
            '-b:a', '192k',
            output_path, '-y'
        ]
        
        result = subprocess.run(
            command, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode == 0:
            print(f"Ghép video thành công bằng FFmpeg siêu tốc!")
            return output_path
        else:
            print(f"FFmpeg ghép video trả về lỗi: {result.stderr}")
            print("Đang tự động chuyển sang dùng MoviePy (chậm hơn do cần re-encode)...")
    except FileNotFoundError:
        print("FFmpeg không có sẵn trong hệ thống (chưa cài đặt hoặc chưa thêm vào PATH).")
        print("Đang tự động chuyển sang dùng MoviePy (chậm hơn do cần re-encode)...")
        
    # Cách 2: Fallback MoviePy (Re-encode)
    try:
        from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip
        video_clip = VideoFileClip(video_path)
        new_audio_clip = AudioFileClip(audio_path)
        
        # Nếu audio mới dài hơn video (do sai số), thì cắt bớt để bằng khớp độ dài video
        if new_audio_clip.duration > video_clip.duration:
            new_audio_clip = new_audio_clip.subclip(0, video_clip.duration)
            
        if video_clip.audio is not None:
            orig_audio = video_clip.audio.volumex(orig_volume)
            new_audio_clip = new_audio_clip.volumex(dub_volume)
            final_audio = CompositeAudioClip([orig_audio, new_audio_clip])
        else:
            final_audio = new_audio_clip.volumex(dub_volume)
            
        final_video = video_clip.set_audio(final_audio)
        
        # Tiến hành xuất video (render).
        final_video.write_videofile(
            output_path, 
            codec="libx264", 
            audio_codec="aac", 
            temp_audiofile=os.path.join(temp_dir, "temp-moviepy-audio.m4a"),
            remove_temp=True,
            logger=None 
        )
        
        video_clip.close()
        new_audio_clip.close()
        final_video.close()
        
        print(f"Ghép video hoàn tất bằng MoviePy!")
        return output_path
        
    except Exception as e:
        print(f"Lỗi khi ghép video: {e}")
        return None
