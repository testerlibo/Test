# -*- coding: utf-8 -*-
import re
import os
import json
import logging
from datetime import datetime
from airtest.core.api import snapshot
from paddleocr import PaddleOCR
from opencc import OpenCC

# 从 config 导入配置
from config import OCR_ERROR_SAVE_DIR

# 过滤日志
logging.getLogger('airtest').setLevel(logging.ERROR)
logging.getLogger('ppocr').setLevel(logging.ERROR)


class CheckTradition:
    """简繁转换检查"""

    def __init__(self,
                 det_model_dir="./checkTraditionWay/models/ch_PP-OCRv4_det_infer",
                 rec_model_dir="./checkTraditionWay/models/ch_PP-OCRv4_rec_infer",
                 cls_model_dir="./checkTraditionWay/models/ch_ppocr_mobile_v2.0_cls_infer",
                 confidence_threshold=0.6):
        self.ocr = PaddleOCR(
            use_angle_cls=True,
            lang="ch",
            device="cpu",
            det_model_dir=det_model_dir,
            rec_model_dir=rec_model_dir,
            cls_model_dir=cls_model_dir,
            det_db_box_thresh=0.3,
            rec_char_dict_path=None
        )
        self.s2t_converter = OpenCC('s2t')
        self.confidence_threshold = confidence_threshold
        self.error_save_dir = OCR_ERROR_SAVE_DIR
        os.makedirs(self.error_save_dir, exist_ok=True)

    def extract_text_from_screen(self):
        """截图 + OCR 识别"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        temp_img = os.path.join(current_dir, "temp_screen.png")

        try:
            snapshot(filename=temp_img, msg="screen")
            if not os.path.exists(temp_img):
                return []

            result = self.ocr.ocr(temp_img, cls=True)
            extracted_texts = []
            if result:
                for line in result:
                    for word_info in line:
                        bbox, (text, conf) = word_info
                        if conf > self.confidence_threshold:
                            extracted_texts.append(text.strip())
            return extracted_texts
        finally:
            if os.path.exists(temp_img):
                try:
                    os.remove(temp_img)
                except:
                    pass

    @staticmethod
    def is_chinese_text(text):
        return bool(re.search(r'[\u4e00-\u9fff]', text))


    def check_tradition(self, text_list):
        """
        检查繁体并存放
        """
        errors = []  # 存放所有错误 {text, expected}

        for value in text_list:
            cleaned = value.replace('\n', '').replace('\r', '').replace(' ', '')

            # 未替换完成
            if '{' in cleaned or 'key' in cleaned or '}' in cleaned:
                errors.append({
                    "text": cleaned,
                    "expected": "【未完成替换】"
                })
                continue

            if not self.is_chinese_text(cleaned):   # 跳过无中文字符文本
                continue

            # 繁简检查
            converted = self.s2t_converter.convert(cleaned)
            if converted != cleaned:        # 这里需要后续补充对照表作为白名单加一个判断
                errors.append({
                    "text": cleaned,
                    "expected": converted
                })

        return errors

    def _save_screen_and_errors(self, errors):
        """
        保存错误截图，写入报告
        """
        if not errors:
            return

        # 截图
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        img_name = f"screen_error_{timestamp}.png"
        img_path = os.path.join(self.error_save_dir, img_name)
        snapshot(filename=img_path, msg="error_screen")

        # 构造报告
        error_detail = [{
            "current_text": e["text"],
            "expected_text": e["expected"]
        } for e in errors]

        report_data = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "screenshot": img_path,
            "error_count": len(errors),
            "errors": error_detail
        }

        # 写入 JSON
        report_path = os.path.join(self.error_save_dir, "error_report.json")
        all_records = []
        if os.path.exists(report_path):
            with open(report_path, "r", encoding="utf-8") as f:
                all_records = json.load(f)

        all_records.append(report_data)

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(all_records, f, ensure_ascii=False, indent=2)

    # ====================== 对外接口 ======================
    def check_current_screen(self, silent=False):
        texts = self.extract_text_from_screen()
        if not texts:
            return []

        errors = self.check_tradition(texts)

        # 有错误 → 保存 1 张截图
        if errors:
            self._save_screen_and_errors(errors)

        if not silent:
            if errors:
                print(f"❌ 本屏发现 {len(errors)} 处错误 | 截图已保存")
            else:
                print("✅ 本屏规范")
        return errors