import redis

def redis_config():
    try:
        REDIS_HOST = "localhost"
        REDIS_PORT = 6379
        REDIS_DATABASE = 0

        rd = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DATABASE, decode_responses=True)
        # decode_responses=True: 바이트 대신 문자열로 받기 편함

        # 연결 테스트 (optional)
        rd.ping()
        print("Redis 연결 성공")
        return rd

    except Exception as e:
        print(f"Redis 연결 실패: {e}")
        return None
