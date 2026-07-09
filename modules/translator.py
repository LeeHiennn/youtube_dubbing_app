import time
import random
import re
from deep_translator import GoogleTranslator

VN_CHARS = re.compile(r'[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]', re.IGNORECASE)

def contains_vietnamese(text):
    """Kiểm tra xem text có chứa ký tự tiếng Việt có dấu hay không."""
    return bool(VN_CHARS.search(text))

def translate_segments(segments):
    """
    Dịch các đoạn văn bản từ tiếng Anh sang tiếng Việt.
    Có cache kết quả, kiểm tra tiếng Việt, và tự động retry (exponential backoff) nếu gặp lỗi.
    """
    translator = GoogleTranslator(source='en', target='vi')
    print("Đang dịch thuật các đoạn văn bản sang tiếng Việt...")
    
    translation_cache = {}
    
    for i, segment in enumerate(segments):
        original_text = segment['text']
        
        # Bỏ qua nếu text rỗng
        if not original_text.strip():
            segment['translated_text'] = ""
            continue
            
        # Kiểm tra code-switching (chứa tiếng Việt)
        if contains_vietnamese(original_text):
            segment['translated_text'] = original_text
            print(f"[{i+1}/{len(segments)}] Bỏ qua dịch (đã chứa TV): {original_text[:30]}...")
            continue
            
        # Kiểm tra cache
        if original_text in translation_cache:
            segment['translated_text'] = translation_cache[original_text]
            print(f"[{i+1}/{len(segments)}] Dịch từ cache: {segment['translated_text'][:30]}...")
            continue
            
        # Thử dịch API với Retry logic (tối đa 3 lần)
        success = False
        for attempt in range(3):
            try:
                translation = translator.translate(original_text)
                segment['translated_text'] = translation
                translation_cache[original_text] = translation
                
                print(f"[{i+1}/{len(segments)}] Dịch thành công: {translation[:30]}...")
                success = True
                
                # Thêm khoảng nghỉ (jitter) để tránh rate limit
                time.sleep(0.3 + random.uniform(0, 0.2))
                break
                
            except Exception as e:
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"Lỗi khi dịch đoạn {i+1} (lần {attempt+1}): {e}. Thử lại sau {wait_time:.2f}s...")
                time.sleep(wait_time)
                
        if not success:
            print(f"[{i+1}/{len(segments)}] Dịch thất bại sau 3 lần thử, giữ nguyên gốc.")
            segment['translated_text'] = original_text
            translation_cache[original_text] = original_text
            
    print("Dịch thuật hoàn tất!")
    return segments
