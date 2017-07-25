import os, sys, re, time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from googletrans import Translator

translator = Translator()

output = open('suppliersPCC.csv','w')
supout = open('suppliers_infoPCC.csv','w')
incilog = open('logs/inciNamesPCC.txt','w')
suplog = open('logs/supNamesPCC.txt','w')
suppliers_infos_url  = {}
acceptTerms = False

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
    #driver.get('http://dir.cosmeticsandtoiletries.com/search/cbr_ing.html')
    #check if we are at http://dir.cosmeticsandtoiletries.com/search/cbr_ing.html
    try:
        #time.sleep(1)
        #print('search item: '+name)
        wait = WebDriverWait(driver, 10)
        elem = wait.until(EC.visibility_of_element_located((By.NAME, "Ingredient")))
        #elem = driver.find_element_by_name('Ingredient')
        elem.clear()
        elem.send_keys(name)
        ok = driver.find_element_by_id('SearchButton')
        ok.click()
        #print('Got to second page')
    except:
        print('Was not able to enter the inci '+name)

    try:
        if not acceptTerms:
            time.sleep(0.5)
            try:
                if driver.find_element_by_name('Accept'):
                    driver.find_element_by_name('Accept').click()
                    time.sleep(0.5)
            except:
                pass
    
        wait = WebDriverWait(driver, 10)
        bidon = wait.until(EC.visibility_of_element_located((By.TAG_NAME, "table")))
        tables = driver.find_elements_by_tag_name('table')
        for i in range(len(tables)):
            try:
                header = tables[i].find_element_by_tag_name('tbody').find_element_by_tag_name('tr').find_element_by_tag_name('th').text
                if header == 'Ingredient Name':
                    resultats = tables[i].find_element_by_tag_name('tbody').find_elements_by_tag_name('tr')
            except Exception as e:
                pass
        if len(resultats) <= 1:
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
            return (name,resultats)
    except:
        return ('Error','')

def get_suppliers_from_inci(mpc, ingredient):
    #ingredient is original name from PME, inci_name is the one that matched the search
    (inci_name,Sups) = submit_search_of(ingredient)

    if inci_name == 'Error':
        incilog.write(ingredient+': could not find any manufacturers\n')
    else:
        matchedName = False
        for i in range(len(Sups)):
            oneResult = Sups[i].find_elements_by_tag_name('td')
            if len(oneResult) <= 1:
                matchedName = False
            elif oneResult[0].text.lower() == inci_name.lower()+' (inci)' or oneResult[0].text.lower() == inci_name.lower()+' (tn)' or (oneResult[0].text == ' ' and matchedName == True):
                print(inci_name+', supplier found as a->text')
                matchedName = True
                add_supplier_to_list(mpc, ingredient, inci_name,oneResult[1].find_element_by_tag_name('a').text)
                #retrieve_supplier(oneResult)
                #add inci_name as first product of supplier in urls
                try:
                    z = suppliers_infos_url[oneResult[1].find_element_by_tag_name('a').text]
                    pass
                except KeyError as k:
                    suppliers_infos_url[oneResult[1].find_element_by_tag_name('a').text] = inci_name

            else:
                matchedName = False

supout.write('Nom du fabricant,Adresse,Courriel,Site Web,No Telephone,No Fax,Autres informations\n')
def retrieve_supplier(oneR):
    #print(suppliers_infos_url)
    #print suppliers_infos_url.keys()
    print 'retrieving'
    sup_ref = oneR[1].find_element_by_tag_name('a')
    sup_name = sup_ref.text
    #check if supplier info are known
    if sup_name in suppliers_infos_url:
        pass
    else:
        sup_ref.click()
        get_supplier_info(sup_name)
        suppliers_infos_url.add(sup_name)
        driver.back()
        print 'we"re back'
        #driver.execute_script("window.history.go(-1)")
        #get_supplier_info(suppliers_infos_url.pop())
def add_supplier_to_list(mpNo, ingredName, inciName, Supplier):
    #print(inciName+','+Supplier+'\n')
    Supplier = re.sub(',', ' ', Supplier, flags=re.IGNORECASE)
    output.write(mpNo+','+ingredName+','+inciName+','+Supplier+'\n')

def get_supplier_info(fab_name,triedBefore=0):
    print 'getting info for: '+fab_name
    wait = WebDriverWait(driver, 10)
    form = wait.until(EC.visibility_of_element_located((By.ID, "SupplierDetailForm")))    
    suppl_adress_list = form.find_elements_by_tag_name('table')[0].find_element_by_tag_name('tbody').find_elements_by_tag_name('tr')
    suppl_contact_list = form.find_elements_by_tag_name('table')[1].find_element_by_tag_name('tbody').find_elements_by_tag_name('tr')     
    if suppl_adress_list[1].text != ' ':
        suplog.write('Error with supplier: '+fab_name+', no whitespace in second')
    i = 3
    informations = {'adress':'','tel':'','fax':'','courriel':'','web':'','other':''}
    while i<len(suppl_adress_list) and suppl_adress_list[i].text != ' ':
        if informations['adress'] != '':
            informations['adress'] = informations['adress']+'; '+suppl_adress_list[i].text
        else:
            informations['adress'] = suppl_adress_list[i].text
        i+=1    
    #while i < len(suppl_contact_list):
        #if()
        #i+=1
    informations = fab_name+','+informations['adress']
    print informations
        #informations = fab_name+','+informations['adress']+','+informations['courriel']+','+informations['web']+','+informations['tel']+','+informations['fax']+','+informations['other']+'\n'
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

print 'Initialization complete'

driver = webdriver.Firefox()
driver.get('http://buyers.personalcarecouncil.org/jsp/BGSearchPage.jsp')
print('Browser opened...')

#login()

list_of_ingredients = open('MP-DB.csv','r')
 
#for line in list_of_ingredients:
min = 0
max = 10
try:
    lastIng = ''
    for i in range(max):
        nextLine = list_of_ingredients.readline()[:-1].split(',')
        mpcode = nextLine[0]
        ing = nextLine[1]
        if i >= min:
            if ing != lastIng:
                get_suppliers_from_inci(mpcode, ing)
            print ('Ingredient search: %2.2f%%  done' %(100.0*(i+1-min)/(max-min)) )
            lastIng = ing
        #print ing
    print suppliers_infos_url
    print len(suppliers_infos_url)
except Exception as e:
    output.close()
    driver.close()
    print e
# names = ['Citric Acid','Acide Stearique','Malic Acid']
# for j in range(len(names)):
#     get_suppliers_from_inci(names[j])
#     print 'Ingredient search: '+str(100.0*(j+1)/len(names))+'%  done'

print 'Ingredient search done'
#retrieve_suppliers()
s = open('suppliers_last_ing.csv','w')
for key in suppliers_infos_url.keys():
    s.write(key+','+re.sub(',', ' ',suppliers_infos_url[key], flags=re.IGNORECASE)+'\n')
print 'Manufacturers infos search done'

#get_suppliers_from_inci('Citric Acid')
#get_suppliers_from_inci('Acide stearique')


output.close()
driver.close()

#     WebDriverWait wait = new WebDriverWait(driver, 10);
# // wait for the new li to appear
# WebElement li = wait.until(ExpectedConditions.elementToBeClickable(By.id("coupon_5")));