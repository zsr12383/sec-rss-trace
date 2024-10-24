import logging
import os
from logging.handlers import TimedRotatingFileHandler

# logs 디렉토리가 없으면 생성
if not os.path.exists('logs'):
    os.makedirs('logs')

# TimedRotatingFileHandler 설정
log_handler = TimedRotatingFileHandler('logs/app.log', when='midnight', interval=1, backupCount=7)
log_handler.suffix = "%Y-%m-%d"  # 로그 파일명에 날짜 추가
log_handler.setLevel(logging.INFO)

# 로그 포맷 설정
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_handler.setFormatter(formatter)

# 로거에 핸들러 추가
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)

# 테스트 로그 작성
logger.info('This is a test log message.')
