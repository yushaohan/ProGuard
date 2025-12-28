import argparse
import base64
import mimetypes
import os
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from openai import OpenAI
from prompts import (
    TEXT_SYSTEM_PROMPT,
    TEXT_USER_PROMPT_TEMPLATE,
    TEXT_IMAGE_SYSTEM_PROMPT,
    TEXT_IMAGE_USER_PROMPT_TEMPLATE,
    IMAGE_SYSTEM_PROMPT,
    IMAGE_USER_PROMPT_TEMPLATE,
)

class ProGuardInference:
    def __init__(self, api_url: str, model_name: str = "ProGuard-7B"):
        self.api_url = api_url
        self.model_name = model_name
        self.client = OpenAI(
            api_key="",
            base_url=api_url
        )
    
    def _image_path_to_data_url(self, image_path: str) -> str:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"File Not Found: {image_path}")
        mime, _ = mimetypes.guess_type(image_path)
        mime = mime or "image/png"
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        return f"data:{mime};base64,{b64}"
    
    def _build_messages(
        self,
        system_prompt: str,
        user_prompt: str,
        image_paths: Optional[List[str]] = None
    ) -> List[Dict]:
        user_content = []
        if image_paths:
            for image_path in image_paths:
                try:
                    data_url = self._image_path_to_data_url(image_path)
                    user_content.append({
                        "type": "image_url",
                        "image_url": {"url": data_url}
                    })
                except Exception as e:
                    print(f"Failed to process image {image_path}: {e}")
                    continue
        
        if user_prompt and user_prompt.strip():
            user_content.append({"type": "text", "text": user_prompt})
        elif image_paths:
            user_content.append({"type": "text", "text": " "})
        else:
            user_content.append({"type": "text", "text": ""})
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        return messages
    
    def _call_api(self, messages: List[Dict], max_tokens: int = 1024, temperature: float = 0.0) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            content = response.choices[0].message.content
            
            if not content or not content.strip():
                raise ValueError("Empty response")
            
            return content
        except Exception as e:
            raise RuntimeError(f"Failed to call API: {type(e).__name__}: {e}")
    
    def infer_text(
        self,
        user_request: str,
        ai_response: Optional[str] = None
    ) -> Dict[str, any]:
        user_prompt = TEXT_USER_PROMPT_TEMPLATE.replace(
            "{{HUMAN_USER}}", user_request
        ).replace(
            "{{AI_ASSISTANT}}", ai_response if ai_response else ""
        )
        messages = self._build_messages(
            TEXT_SYSTEM_PROMPT,
            user_prompt,
            image_paths=None
        )
        raw_response = self._call_api(messages)
        return {
            "modality": "text",
            "raw_response": raw_response,
        }
    
    def infer_text_image(
        self,
        user_request: str,
        image_path: str,
        ai_response: Optional[str] = None
    ) -> Dict[str, any]:
        user_prompt = TEXT_IMAGE_USER_PROMPT_TEMPLATE.replace(
            "{{HUMAN_USER}}", user_request
        ).replace(
            "{{AI_ASSISTANT}}", ai_response if ai_response else ""
        )
        messages = self._build_messages(
            TEXT_IMAGE_SYSTEM_PROMPT,
            user_prompt,
            image_paths=[image_path]
        )
        raw_response = self._call_api(messages)
        return {
            "modality": "text-image",
            "raw_response": raw_response,
        }
    
    def infer_image(
        self,
        image_path: str
    ) -> Dict[str, any]:
        user_prompt = IMAGE_USER_PROMPT_TEMPLATE.replace(
            "{{HUMAN_USER}}", ""
        ).replace(
            "{{AI_ASSISTANT}}", ""
        )
        messages = self._build_messages(
            IMAGE_SYSTEM_PROMPT,
            user_prompt,
            image_paths=[image_path]
        )

        raw_response = self._call_api(messages)        
        return {
            "modality": "image",
            "raw_response": raw_response,
        }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api_url", type=str, required=True)
    parser.add_argument("--model_name", type=str, default="ProGuard-7B")
    parser.add_argument("--mode", type=str, required=True, choices=["text", "text-image", "image"])
    parser.add_argument("--user_request", type=str, default="")
    parser.add_argument("--ai_response", type=str, default=None)
    parser.add_argument("--image_path", type=str, default=None)
    args = parser.parse_args()
    if args.mode in ["text-image", "image"] and not args.image_path:
        parser.error(f"{args.mode} mode requires --image_path parameter")
    if args.mode in ["text", "text-image"] and not args.user_request:
        parser.error(f"{args.mode} mode requires --user_request parameter")
    inferencer = ProGuardInference(args.api_url, args.model_name)
    try:
        if args.mode == "text":
            result = inferencer.infer_text(args.user_request, args.ai_response)
        elif args.mode == "text-image":
            result = inferencer.infer_text_image(
                args.user_request,
                args.image_path,
                args.ai_response
            )
        elif args.mode == "image":
            result = inferencer.infer_image(args.image_path)
        else:
            raise ValueError(f"Unknown mode: {args.mode}")
        
        print("\n" + "="*60)
        print("Result")
        print("="*60)
        print(f"Modality: {result['modality']}")
        print("\nResponse:")
        print("-"*60)
        print(result['raw_response'])
        print("="*60)
        
    except Exception as e:
        print(f"Error : {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())