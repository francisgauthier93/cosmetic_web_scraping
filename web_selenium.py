import os, sys, re, time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from googletrans import Translator

translator = Translator()

output = open('suppliers.csv','w')
supout = open('suppliers_info.csv','w')
incilog = open('logs/inciNames.txt','w')
suplog = open('logs/supNames.txt','w')
suppliers_infos_url  = {}


def add_supplier_to_list(inciName, Supplier):
    #print(inciName+','+Supplier+'\n')
    output.write(inciName+','+Supplier+'\n')

def get_supplier_info(url,fab_name,triedBefore=0):
    if url is None:
        pass
    else:
        driver.get(url)
        time.sleep(2)
        side = driver.find_element_by_class_name('col-sm-6')
        #print type(side)
        informations = side.find_element_by_tag_name('p').text
        informations = parseInfos(informations)
        if informations['adress'] == ';':
            suplog.write(fab_name+' : '+url+'\n')
        informations = fab_name+','+informations['adress']+','+informations['courriel']+','+informations['web']+','+informations['tel']+','+informations['fax']+','+informations['other']+'\n'
        supout.write(informations)

def parseInfos(s):
    lis = s.split('\n')
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
    return infos


def login():
    time.sleep(1)
    username = driver.find_element_by_id('username')
    username.send_keys('frankigauthier93@gmail.com')
    pword = driver.find_element_by_id('password')
    pword.send_keys('pointmi')
    pword.send_keys(Keys.RETURN)
    #pword.submit()
    print('Login successful')
    time.sleep(1)

def submit_search_of(name, translated = False):
    driver.get('http://dir.cosmeticsandtoiletries.com/search/cbr_ing.html')
    #check if we are at http://dir.cosmeticsandtoiletries.com/search/cbr_ing.html
    try:
        elems = driver.find_elements_by_class_name('form-control')
        elems[1].send_keys(name)
        elems[1].send_keys(Keys.RETURN)
        #print('Got to second page')
    except:
        print('Was not able to enter the inci '+name)

    try:
        delay = 2
        # try:
        #     myElem = WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.ID, 'resultsTable')))
        #     print "Page is ready!"
        # except TimeoutException:
        #     print "Loading took too much time!"

        #results = driver.find_element_by_id('resultsTable')
        #print 'sleep'
        time.sleep(delay)
        #print 'wake'
        ##Check if we got results
        resultats = driver.find_element_by_id('results').find_element_by_tag_name('p').text
        p = re.compile('\d+')
        numb = p.findall(resultats)[0]
        #print numb+' resultats. trouves'
        if int(numb) == 0:
            #print('No results for '+name)
            if not translated:
                try:
                    traduc = translator.translate(name, src='fr', dest='en').text
                except:
                    traduc = ''
                    print(name+': translation failed')
                return submit_search_of(traduc, True)
            else:
                raise Exception('Both translations failed')
        else:
            results = driver.find_element_by_tag_name('table')
            resultsList = results.find_element_by_tag_name('tbody').find_elements_by_tag_name('tr')
            #print(name+', found '+str(len(resultsList))+' results')
            return (name,resultsList)
    except:
        #print name+": could not get the results"
        return ('Error','')

def get_suppliers_from_inci(ingredient):
    (inci_name,Sups) = submit_search_of(ingredient)
    if inci_name == 'Error':
        incilog.write(ingredient+': could not find any manufacturers\n')
    else:
        for i in range(len(Sups)):
            oneResult = Sups[i].find_elements_by_tag_name('td')
            if oneResult[0].find_element_by_tag_name('a').text.lower() == inci_name.lower():
                #print(inci_name+', supplier found as a->text')
                add_supplier_to_list(inci_name,oneResult[1].find_element_by_tag_name('a').text)
                suppliers_infos_url[oneResult[1].find_element_by_tag_name('a').text] = oneResult[1].find_element_by_tag_name('a').get_attribute('href')
            elif oneResult[0].text.lower() == inci_name.lower():
                #print(inci_name+', supplier found as text')
                add_supplier_to_list(inci_name,oneResult[1].text)


def retrieve_suppliers():
    #print(suppliers_infos_url)
    #print suppliers_infos_url.keys()
    #header
    supout.write('Nom du fabricant,Adresse,Courriel,Site Web,No Telephone,No Fax,Autres informations\n')
    numbSup = len(suppliers_infos_url)
    for i in range(len(suppliers_infos_url)):
        currKey = suppliers_infos_url.keys()[0]
        get_supplier_info(suppliers_infos_url.pop(suppliers_infos_url.keys()[0], None), currKey)
        print ('Manufacturers search: '+str(round(100.0*(i+1)/numbSup,2))+'%% done')
    #get_supplier_info(suppliers_infos_url.pop())

print 'Initialization complete'

driver = webdriver.Firefox()
driver.get('http://dir.cosmeticsandtoiletries.com/main/login.html')
print('Browser opened...')

login()

list_of_ingredients = open('MP-DB.csv','r')
#for line in list_of_ingredients:
min = 273
max = 400
try:
    lastIng = ''
    for i in range(max):
        ing = list_of_ingredients.readline()[:-1]
        if i >= min:
            if ing != lastIng:
                get_suppliers_from_inci(ing)
            print ('Ingredient search: %2.2f%%  done' %(100.0*(i+1-min)/(max-min)) )
            lastIng = ing
        #print ing
except Exception as e:
    output.close()
    driver.close()
    print e
# names = ['Citric Acid','Acide Stearique','Malic Acid']
# for j in range(len(names)):
#     get_suppliers_from_inci(names[j])
#     print 'Ingredient search: '+str(100.0*(j+1)/len(names))+'%  done'

print 'Ingredient search done'
retrieve_suppliers()
print 'Manufacturers infos search done'

#get_suppliers_from_inci('Citric Acid')
#get_suppliers_from_inci('Acide stearique')


output.close()
driver.close()

#     WebDriverWait wait = new WebDriverWait(driver, 10);
# // wait for the new li to appear
# WebElement li = wait.until(ExpectedConditions.elementToBeClickable(By.id("coupon_5")));