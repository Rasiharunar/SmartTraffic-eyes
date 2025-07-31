import cv2
from pytube import YouTube

yt = YouTube("https://www.youtube.com/watch?v=wqctLW0Hb_0&pp=ygUPdHJhZmZpYyB2ZWhpY2xl")
stream = yt.streams.filter(res="360p", mime_type="video/mp4").first()
capture = cv2.VideoCapture(stream.url)

while True:
    ret, frame = capture.read()
    if not ret:
        print("Stream tidak terbaca")
        break

    cv2.imshow('YouTube Stream', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

capture.release()
cv2.destroyAllWindows()