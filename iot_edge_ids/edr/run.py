import threading
import detector
import response_handler

if __name__ == "__main__":
    t1 = threading.Thread(target=detector.main)
    t2 = threading.Thread(target=response_handler.main)
    
    t1.start()
    t2.start()
    
    t1.join()
    t2.join()
