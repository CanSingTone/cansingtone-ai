import requests

url = 'http://3.36.170.145:5000//upload-mp3'  # 서버주소는 애플리케이션이 실행되는 주소
files = {'file': open('sample_data/테스트.mp3', 'rb')}  # 업로드할 mp3 파일의 경로와 파일명
data = {'user_id': '12345'}

response = requests.post(url, files=files, data=data)

print(response)
print(response.text)  # 서버의 응답 출력
