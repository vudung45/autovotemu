import pytesseract
import cv2
import sys
import argparse
import numpy as np
try:
    import Image
except ImportError:
    from PIL import Image
from subprocess import check_output

special = ["W","K","S","Z","O"]

def solve_image(image, debug = False):
	image[np.where((image==[255]))] = [0]
	processed = np.zeros([len(image),len(image[0]),3],dtype=np.uint8)
	processed.fill(255) # or img[:] = 255
	lower_black = np.array([0])
	upper_black = np.array([50])
	mask = cv2.inRange(image, lower_black, upper_black)
	_, contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
	cv2.drawContours(processed, contours, -1, (0,0,0), -1)
	lower_black = np.array([180])
	upper_black = np.array([255])
	mask = cv2.inRange(image, lower_black, upper_black)
	_, contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
	cv2.drawContours(processed, contours, -1, (0,0,0), -1)
	if debug:
		cv2.imshow("Ok", processed)
		cv2.waitKey(1000)
	return pytesseract.image_to_string(processed).replace(" ","").replace(")","J").replace("¢","c").replace("$","S").replace("\n","")



def resolve(path, extension=".png"):
	new_path = path.split(extension)[0] + "_resampled"+extension
	check_output(['convert', path, '-resample', '200', new_path])
	image = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
	capital = solve_image(image)
	result = list(capital)
	for c in result:
		if c.upper() in special:
			non_capital = solve_image(image[int(len(image)/2.5):,:]).upper()
			for i, c1 in enumerate(non_capital):
				if c1.upper() in result and c1.upper() in special:
					index = result.index(c1)
					if(index >= i):
						result[index] = c1.lower()
			break

	return "".join(result)

if __name__=="__main__":
	argparser = argparse.ArgumentParser()
	argparser.add_argument('path',help = 'Captcha file path')

	args = argparser.parse_args()
	path = args.path
	print('Resolving Captcha')
	captcha_text = resolve(path)
	print('Extracted Text',captcha_text)