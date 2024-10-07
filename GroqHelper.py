from groq import Groq
import logging_config
import logging

from request_helper import Request_Helper


class GroqHelper():
    @staticmethod
    def ask_groq(text: str, groq_msg: str, groq_client: Groq, request_helper: Request_Helper):
        new_text = groq_msg + "\n\n\n" + text
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
            logging.error(e)
            request_helper.send_to_slack(str(e))

    @staticmethod
    def get_slack_msg(signum: str):
        # if signum
        pass
