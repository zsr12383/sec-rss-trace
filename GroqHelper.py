from groq import Groq
import logging_config
import logging

from requesthelper import RequestHelper


class GroqHelper():
    @staticmethod
    def ask_groq(text: str, groq_msg: str, groq_client: Groq, request_helper: RequestHelper):
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
        return None

    @staticmethod
    def get_slack_msg(signum: str):
        # if signum
        pass

    @staticmethod
    def send_to_slack_groq_answer(entry, groq_answer, request_helper: RequestHelper):
        message = f"New entry found:\n\tTitle: {entry['title']}\n\tLink: {entry['link']}\n\tGroq_Answer: {groq_answer}"
        request_helper.send_to_slack(message)
