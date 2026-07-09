import os
import sys
import io
import json
import shutil

# Đảm bảo in được tiếng Việt trên console Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from modules.downloader import download_media
from modules.voice_separator import separate_full
from modules.stt_engine import transcribe_audio
from modules.translator import translate_segments
from modules.tts_engine import generate_voiceover
from modules.media_merger import merge_audio_with_video
import modules.tts_engine as tts_engine 
from moviepy.editor import VideoFileClip

def save_checkpoint(temp_dir, name, data):
    path = os.path.join(temp_dir, f'checkpoint_{name}.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_checkpoint(temp_dir, name):
    path = os.path.join(temp_dir, f'checkpoint_{name}.json')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def cleanup_temp_files():
    """Dọn dẹp xóa mọi file rác trong thư mục temp/ sau khi hoàn thành thành công."""
    base_dir = os.path.dirname(__file__)
    temp_dir = os.path.join(base_dir, 'temp')
    
    if not os.path.exists(temp_dir):
        return
        
    try:
        shutil.rmtree(temp_dir)
        print("Đã dọn dẹp sạch sẽ thư mục lưu trữ tạm.")
    except Exception as e:
        print(f"Không thể xóa thư mục tạm: {e}")

def process_video(url, voice_choice, progress=None, model_size="small", orig_audio_volume=0.3, cancel_event=None, separate_vocals_flag=True):
    """
    Quy trình xử lý video, hỗ trợ Gradio Progress Bar, Checkpointing, Cancel Event.
    """
    if progress: progress(0, desc="Bắt đầu quá trình...")
    
    # Thiết lập giọng đọc tùy theo lựa chọn trên giao diện
    if voice_choice == "Nam (Nam Minh)":
        tts_engine.VOICE_NAME = "vi-VN-NamMinhNeural"
    else:
        tts_engine.VOICE_NAME = "vi-VN-HoaiMyNeural"

    base_dir = os.path.dirname(__file__)
    temp_dir = os.path.join(base_dir, 'temp')
    
    url_file = os.path.join(temp_dir, 'current_url.txt')
    if os.path.exists(url_file):
        with open(url_file, 'r', encoding='utf-8') as f:
            saved_url = f.read().strip()
        if saved_url != url:
            print("URL mới được phát hiện, tiến hành dọn dẹp data cũ...")
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass
                
    os.makedirs(temp_dir, exist_ok=True)
    with open(os.path.join(temp_dir, 'current_url.txt'), 'w', encoding='utf-8') as f:
        f.write(url)
    
    success = False
    try:
        if cancel_event and cancel_event.is_set(): return
        
        # Bước 1: Tải Media
        if progress: progress(0.05, desc="Đang tải Video & Audio từ YouTube...")
        print(f"Bắt đầu xử lý URL: {url}")
        
        video_path = os.path.join(temp_dir, 'video.mp4')
        audio_path = os.path.join(temp_dir, 'video.mp3')
        if os.path.exists(video_path) and os.path.exists(audio_path):
            print("Phục hồi từ file media đã tải...")
        else:
            media_paths = download_media(url)
            video_path = media_paths['video']
            audio_path = media_paths['audio']
            
        if cancel_event and cancel_event.is_set(): return
        
        # Bước 1.5: Tách giọng nói (nếu bật)
        stt_audio_path = audio_path
        no_music_path = None
        vocal_path = audio_path
        if separate_vocals_flag:
            if progress: progress(0.15, desc="Đang tách giọng nói khỏi nhạc nền...")
            sep_result = separate_full(audio_path, temp_dir)
            stt_audio_path = sep_result["vocals"]
            vocal_path = sep_result["vocals"]
            no_music_path = sep_result["no_music"]
        else:
            print("Bỏ qua bước tách giọng nói.")

        if cancel_event and cancel_event.is_set(): return
        
        # Bước 2: STT (Speech-to-Text)
        if progress: progress(0.3, desc=f"AI đang bóc băng lời nói (Whisper {model_size})...")
        
        segments = load_checkpoint(temp_dir, 'stt')
        if segments:
            print("Phục hồi từ checkpoint STT...")
        else:
            segments = transcribe_audio(stt_audio_path, model_size=model_size)
            save_checkpoint(temp_dir, 'stt', segments)
            
        if cancel_event and cancel_event.is_set(): return
        
        # Kiểm tra Empty Speech
        if not segments:
            raise Exception("Video không chứa giọng nói hoặc không thể nhận diện được.")
            
        total_speech_duration = sum(seg['end'] - seg['start'] for seg in segments)
        if total_speech_duration < 1.0:
            raise Exception("Video không chứa giọng nói hoặc không thể nhận diện được.")
            
        # Bước 3: Dịch thuật
        if progress: progress(0.5, desc="Đang dịch ngữ nghĩa sang tiếng Việt...")
        
        translated_segments = load_checkpoint(temp_dir, 'translated')
        if translated_segments:
            print("Phục hồi từ checkpoint dịch thuật...")
        else:
            translated_segments = translate_segments(segments)
            save_checkpoint(temp_dir, 'translated', translated_segments)
            
        if cancel_event and cancel_event.is_set(): return
        
        # Bước 4: TTS (Text-to-Speech)
        if progress: progress(0.7, desc=f"Đang sinh giọng đọc AI ({voice_choice})...")
        video_duration = None
        try:
            video_clip = VideoFileClip(video_path)
            video_duration = video_clip.duration
            video_clip.close()
        except:
            pass
        merged_audio_path = generate_voiceover(translated_segments, video_duration=video_duration)

        
        if not merged_audio_path or not os.path.exists(merged_audio_path):
            raise Exception("Không tạo được giọng đọc (có thể video gốc không có tiếng nói).")
            
        if cancel_event and cancel_event.is_set(): return
            
        # Bước 5: Ghép nối vào video
        if progress: progress(0.9, desc="Đang ghép đè âm thanh tiếng Việt vào Video gốc...")
        final_video = merge_audio_with_video(video_path, merged_audio_path, orig_volume=orig_audio_volume)
        
        if progress: progress(1.0, desc="Hoàn tất!")
        print(f"Xử lý thành công! File xuất ra tại: {final_video}")
        success = True
        return {
            "video": final_video,
            "vocal": vocal_path,
            "no_music": no_music_path,
            "tts_audio": merged_audio_path,
            "segments": translated_segments
        }
        
    except Exception as e:
        print(f"Lỗi hệ thống: {e}")
        raise Exception(f"Đã xảy ra lỗi: {str(e)}")
    finally:
        if cancel_event and cancel_event.is_set():
            print("Pipeline bị hủy bởi người dùng")
        if success:
            pass # Bỏ cleanup_temp_files() tự động để GUI còn đọc được file audio
            # cleanup_temp_files()

if __name__ == "__main__":
    # Test CLI (Dùng cho việc gõ lệnh trên terminal nếu không dùng GUI)
    print("=" * 60)
    print("===  PIPELINE LỒNG TIẾNG YOUTUBE TỰ ĐỘNG (EN -> VI)  ===")
    print("=" * 60)
    test_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
    process_video(test_url, "Nữ (Hoài My)", model_size="small")
