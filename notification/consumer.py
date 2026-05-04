from database import redis
import time

key1 = 'order_completed'   
key2 = 'refund_order'      
group = 'notification-group'

try:
    redis.xgroup_create(key1, group, mkstream=True)
except:
    print(f'Group already exists for {key1}')

try:
    redis.xgroup_create(key2, group, mkstream=True)
except:
    print(f'Group already exists for {key2}')

print("Notification Service started. Listening for events...")

while True:
    try:
        for stream_key in [key1, key2]:
            results = redis.xreadgroup(group, stream_key, {stream_key: '>'}, count=1, block=1000)
            
            if results:
                for result in results:
                    message_data = result[1][0][1]
                    order_id = message_data.get('pk', message_data.get('product_id', 'unknown'))
                    
                    if stream_key == 'order_completed':
                        print(f"📧 OBAVEŠTENJE: Porudžbina {order_id} je uspešno kreirana i plaćena!")
                    elif stream_key == 'refund_order':
                        print(f"📧 OBAVEŠTENJE: Porudžbina {order_id} je refundirana. Novac vraćen na račun.")
                        
    except Exception as e:
        print(f"Notification consumer error: {e}")
        time.sleep(1)

