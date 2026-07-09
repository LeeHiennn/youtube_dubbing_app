import gradio as gr
import threading
import subprocess
import json
from main import process_video

import queue
import sys

cancel_event = threading.Event()

class OutputCapture:
    def __init__(self, original_stdout, q):
        self.original_stdout = original_stdout
        self.q = q
    def write(self, text):
        self.original_stdout.write(text)
        if text.strip():
            self.q.put(text)
    def flush(self):
        self.original_stdout.flush()

def detect_duration(url):
    if not url or ("youtube.com" not in url and "youtu.be" not in url):
        return "⏱ Duration: —"
        
    try:
        import os
        cookie_file = os.path.join(os.path.dirname(__file__), 'cookies.txt')
        if os.path.exists(cookie_file):
            cmd = ['yt-dlp', '--cookies', cookie_file, '--print', 'duration', url]
        else:
            cmd = ['yt-dlp', '--cookies-from-browser', 'chrome', '--print', 'duration', url]
            
        result = subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=10
        )
        duration = int(result.stdout.strip())
        mins, secs = divmod(duration, 60)
        if duration > 1800:
            warning = "⚠️ Video dài >30 phút — sẽ chunk và dùng Whisper tiny"
        elif duration > 600:
            warning = "⚠️ Video dài >10 phút — sẽ chunk tự động"
        else:
            warning = "✅ OK"
        return f"⏱ Duration: {mins}:{secs:02d} ({warning})"
    except:
        return "⏱ Duration: không xác định"

def run_dubbing(url, voice, whisper_model, orig_volume, separate_vocals_flag, progress=gr.Progress()):
    global cancel_event
    cancel_event.clear()
    
    if not url or ("youtube.com" not in url and "youtu.be" not in url):
        raise gr.Error("Link YouTube không hợp lệ!")
    
    q = queue.Queue()
    original_stdout = sys.stdout
    capture = OutputCapture(original_stdout, q)
    sys.stdout = capture
    
    log_history = ""
    yield log_history, None, None, None, None, None
    
    def worker():
        try:
            result_dict = process_video(
                url, voice,
                model_size=whisper_model,
                orig_audio_volume=orig_volume,
                cancel_event=cancel_event,
                progress=progress,
                separate_vocals_flag=separate_vocals_flag
            )
            q.put(("DONE", result_dict))
        except Exception as e:
            q.put(("ERROR", str(e)))
            
    t = threading.Thread(target=worker)
    t.start()
    
    try:
        while True:
            try:
                msg = q.get(timeout=0.2)
                if isinstance(msg, tuple):
                    status, result = msg
                    if status == "ERROR":
                        raise gr.Error(result)
                    else:
                        # process dataframe
                        segments = result.get("segments", [])
                        df_data = []
                        for seg in segments:
                            start_str = f"{int(seg['start']//60)}:{int(seg['start']%60):02d}"
                            end_str = f"{int(seg['end']//60)}:{int(seg['end']%60):02d}"
                            df_data.append([f"{start_str} - {end_str}", seg.get('text', ''), seg.get('translated_text', '')])

                        yield log_history, result.get("video"), result.get("no_music"), result.get("vocal"), result.get("tts_audio"), df_data
                        break
                else:
                    log_history += msg + "\n"
                    lines = log_history.strip().split("\n")
                    if len(lines) > 20:
                        log_history = "\n".join(lines[-20:]) + "\n"
                    yield log_history, None, None, None, None, None
            except queue.Empty:
                if not t.is_alive():
                    break
                yield log_history, None, None, None, None, None
    finally:
        sys.stdout = original_stdout

def cancel_processing():
    global cancel_event
    cancel_event.set()

with gr.Blocks(title="AI YouTube Dubber", theme=gr.themes.Soft()) as app:
    gr.Markdown("# 🎙️ Trợ lý Lồng Tiếng YouTube AI")
    gr.Markdown("Lồng tiếng Anh → Việt, giữ tiếng gốc, xử lý video dài, chuẩn hóa phát âm.")
    
    with gr.Row():
        url_input = gr.Textbox(
            label="🔗 Link YouTube", scale=3,
            placeholder="https://www.youtube.com/watch?v=..."
        )
        duration_display = gr.Markdown("⏱ Duration: —", scale=1)
    
    with gr.Row():
        voice_dropdown = gr.Dropdown(
            choices=["Nữ (Hoài My)", "Nam (Nam Minh)"],
            value="Nữ (Hoài My)", label="Giọng đọc", scale=1
        )
        whisper_dropdown = gr.Dropdown(
            choices=["tiny", "base", "small", "medium"],
            value="small", label="Model Whisper", scale=1
        )
        volume_slider = gr.Slider(
            minimum=0, maximum=1, value=0.3, step=0.05,
            label="Âm lượng tiếng gốc", scale=1
        )
        separate_vocals_checkbox = gr.Checkbox(
            label="Tách giọng nói (Demucs)", value=True,
            scale=1
        )
    
    with gr.Row():
        submit_btn = gr.Button("🚀 Bắt đầu Lồng Tiếng", variant="primary")
        cancel_btn = gr.Button("⏹ Hủy", variant="stop")
    
    log_output = gr.Textbox(
        label="📋 Log", lines=8, max_lines=20,
        placeholder="Log (xem console để biết chi tiết)...",
        interactive=False
    )
    
    gr.Markdown("## 🎬 Video & Âm thanh chi tiết")
    with gr.Row():
        with gr.Column(scale=2):
            video_output = gr.Video(label="🎬 Thành quả (Video + Audio trộn)")
        with gr.Column(scale=1):
            no_music_output = gr.Audio(label="🌿 Âm thanh nền (Không có tiếng nói)")
            vocal_output = gr.Audio(label="🗣 Giọng nói gốc (Vocal EN)")
            tts_output = gr.Audio(label="🔊 Lồng tiếng Việt (TTS VI)")

    gr.Markdown("## 📝 Transcript đã dịch (Bảng kiểm tra)")
    transcript_output = gr.Dataframe(
        headers=["Thời gian", "Tiếng Anh (Gốc)", "Tiếng Việt (Đã dịch)"],
        wrap=True,
        interactive=False
    )
    
    # Events
    url_input.change(fn=detect_duration, inputs=url_input, outputs=duration_display)
    
    submit_btn.click(
        fn=run_dubbing,
        inputs=[url_input, voice_dropdown, whisper_dropdown, volume_slider, separate_vocals_checkbox],
        outputs=[log_output, video_output, no_music_output, vocal_output, tts_output, transcript_output]
    )
    
    cancel_btn.click(
        fn=cancel_processing,
        inputs=None,
        outputs=None
    )

if __name__ == "__main__":
    app.launch(inbrowser=True)
