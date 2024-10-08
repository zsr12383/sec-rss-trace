import time

from groq import Groq
import logging_config
import logging
import re

from requesthelper import RequestHelper


class GroqHelper():
    @staticmethod
    def ask_groq(text: str, groq_msg: str, groq_client: Groq, request_helper: RequestHelper):
        new_text = groq_msg + "\n\n\n" + text
        for i in range(3):
            try:
                chat_completion = groq_client.chat.completions.create(
                    messages=[
                        {
                            "role": "user",
                            "content": new_text
                        }
                    ],
                    model="llama-3.1-70b-versatile"
                )
                return chat_completion.choices[0].message.content
            except Exception as e:
                if i < 3 and hasattr(e, 'status_code') and e.status_code == 429:
                    if 'error' in e.body and 'message' in e.body['error']:
                        error_message = e.body['error']['message']
                        limit_match = re.search(r'Limit (\d+)', error_message)
                        # used_match = re.search(r'Used (\d+)', error_message)
                        requested_match = re.search(r'Requested (\d+)', error_message)
                        wait_time_match = re.search(r'Please try again in (\d+m\d+\.\d+s)', error_message)
                        if limit_match and requested_match and wait_time_match:
                            limit = int(limit_match.group(1))
                            # used = int(used_match.group(1))
                            requested = int(requested_match.group(1))
                            wait_time_str = wait_time_match.group(1)

                            # 대기 시간을 초(second)로 변환
                            m = re.match(r'(\d+)m([\d.]+)s', wait_time_str)
                            if m:
                                minutes = int(m.group(1))
                                seconds = float(m.group(2))
                                wait_seconds = minutes * 60 + seconds + 1
                            else:
                                wait_seconds = 5

                            if requested <= limit:
                                logging.info(f"{wait_seconds}초 동안 대기한 후 재시도합니다.")
                                time.sleep(wait_seconds)
                                continue
                logging.error(e)
                request_helper.send_to_slack(str(e))
                break
        return None
