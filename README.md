
# Ext4 FileSystem Parser Python 2.7

	Jungwan Choi
	Korea Univ. CYDF
	baio2033@korea.ac.kr

# Usage

	python parser.py <image.dd>

# Description
	
	ext4 파일시스템을 해석해주는 파이썬 툴입니다.
	root directory 부터 순회가 가능하며 파일 추출 기능이 있습니다.(단, depth 가 0 인 파일에 한하여 추출이 가능함)
	Usage 에 나온대로 파서를 실행하고 원하는 디렉토리 또는 파일의 번호를 입력합니다.
	디렉토리를 선택할 경우 디렉토리 엔트리를 해석하여 출력해주며, 
	파일을 선택할 경우 해당 파일을 export 폴더에 해당 파일과 동일한 파일명으로 추출합니다.
