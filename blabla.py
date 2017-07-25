import re
from googletrans import Translator

translator = Translator()
print(translator.translate('acide stearique', src='fr', dest='en').text)

print '-----'
f = open('prinova.txt','r+')
string = f.read()
lis = string.split('\n')
infos = {'adress':'','tel':'','fax':'','courriel':'','web':'','other':''}
telFound = False
TelPattern = re.compile('Tel.*')
FaxPattern = re.compile('Fax.*')
CouPattern = re.compile('.*@.*')
WebPattern = re.compile('www\..*')
for i in range(len(lis)):
	match = TelPattern.match(lis[i])
	if match or telFound:
		telFound = True
		if TelPattern.match(lis[i]):
			telNum = lis[i]
			telNum = telNum.split('Tel: ')[1]
			if infos['tel'] == '':
				infos['tel']= infos['tel']+telNum
				infos['adress']= infos['adress'][:-1]
			else:
				infos['tel']= infos['tel']+'; '+telNum
		elif FaxPattern.match(lis[i]):
			infos['fax'] = lis[i].split('Fax: ')[1]
		elif CouPattern.match(lis[i]):
			infos['courriel'] = lis[i]
		elif WebPattern.match(lis[i]):
			infos['web'] = lis[i]
		else:
			if infos['other'] == '':
				infos['other'] = lis[i]
			else:
				infos['other'] = infos['other']+'; '+lis[i]
	else:
		infos['adress'] = infos['adress']+lis[i]+';'

infos['adress'] = re.sub(',', ' ', infos['adress'], flags=re.IGNORECASE)		
print lis
print'----'
print infos