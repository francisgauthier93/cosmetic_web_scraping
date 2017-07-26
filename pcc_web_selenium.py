import os, sys, re, time, shutil
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from googletrans import Translator
reload(sys)
sys.setdefaultencoding('utf-8')

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

def extractSupLink(tdTag):
    ref = tdTag.find_element_by_tag_name('a').get_attribute('href')
    ref = ref[24:-1].split(',')
    ref[0] = re.sub('\'','',ref[0], flags=re.IGNORECASE)
    ref[1] = re.sub('\'','',ref[1], flags=re.IGNORECASE)
    return (ref[0],re.sub('%20', '+' ,ref[1], flags=re.IGNORECASE))

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
                #print(inci_name+', supplier found as a->text')
                matchedName = True
                add_supplier_to_list(mpc, ingredient, inci_name,oneResult[1].find_element_by_tag_name('a').text)
                (supNo, ingred) = extractSupLink(oneResult[1])
                #print (supNo,ingred)
                #retrieve_supplier(oneResult)
                #add inci_name as first product of supplier in urls
                try:
                    z = suppliers_infos_url[supNo]
                except KeyError as k:
                    suppliers_infos_url[supNo] = ingred

            else:
                matchedName = False

supout.write('Nom du fournisseur,Adresse,Courriel,Site Web,No Telephone,No Fax,Autres informations\n')
def retrieve_suppliers():
    total = len(suppliers_infos_url)
    i = 0
    for no in suppliers_infos_url.keys():
        url = 'http://buyers.personalcarecouncil.org/jsp/SupplierDtlPage.jsp?pageName=BGSearchResultPage&SupplierID='+no+'&Ingredient='+suppliers_infos_url[no]
        #print url
        i+=1
        get_supplier_info(url)
        print('Suppliers search: %2.2f%%  done' %(100.0*(i)/(total)) ) 
        
def add_supplier_to_list(mpNo, ingredName, inciName, Supplier):
    #print(inciName+','+Supplier+'\n')
    Supplier = re.sub(',', ' ', Supplier, flags=re.IGNORECASE)
    output.write(mpNo+','+ingredName+','+inciName+','+Supplier+'\n')

def get_supplier_info(url,triedBefore=0):
    
    driver.get(url)
    wait = WebDriverWait(driver, 10)
    form = wait.until(EC.visibility_of_element_located((By.ID, "SupplierDetailForm")))    
    suppl_adress_list = form.find_elements_by_tag_name('table')[0].find_element_by_tag_name('tbody').find_elements_by_tag_name('tr')
    suppl_contact_list = form.find_elements_by_tag_name('table')[1].find_element_by_tag_name('tbody').find_elements_by_tag_name('tr')     
    if suppl_adress_list[1].text != ' ':
        suplog.write('Error with supplier: '+url+', no whitespace in second')
    fab_name = re.sub(',',' ',suppl_adress_list[2].text , flags= re.IGNORECASE)
    i = 3
    informations = {'adress':'','tel':'','fax':'','courriel':'','web':'','other':''}
    while i<len(suppl_adress_list) and suppl_adress_list[i].text != ' ':
        if informations['adress'] != '':
            informations['adress'] = informations['adress']+'; '+re.sub(',',' ',suppl_adress_list[i].text,flags=re.IGNORECASE)
        else:
            informations['adress'] = re.sub(',',' ',suppl_adress_list[i].text,flags=re.IGNORECASE)
        i+=1    
    #while i < len(suppl_contact_list):
        #if()
        #i+=1
    #informations = fab_name+','+informations['adress']
    for i in range(len(suppl_contact_list)):
        datas = suppl_contact_list[i].find_elements_by_tag_name('td')
        if datas[0].text == 'Phone :':
            informations['tel'] = datas[2].text
        elif datas[0].text == 'Fax :':
            informations['fax'] = datas[2].text
        elif datas[0].text == 'Website :':
            informations['web'] = datas[2].text
        else:
            informations['other'] = informations['other']+'; '+suppl_contact_list[i].text

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

#################################################
print 'Initialization complete'

driver = webdriver.Firefox()
driver.get('http://buyers.personalcarecouncil.org/jsp/BGSearchPage.jsp')
print('Browser opened...')

#login()

list_of_ingredients = open('MP-DB.csv','r')
 
#for line in list_of_ingredients:
min = 0
max = 900
backUpCycle = 50
try:
    lastBackUp = 0
    lastIng = ''
    for i in range(max):
        try:
            nextLine = list_of_ingredients.readline()[:-1].split(',')
        except:
            break
        mpcode = nextLine[0]
        ing = nextLine[1]
        if i >= min:
            if ing != lastIng:
                get_suppliers_from_inci(mpcode, ing)
            print ('Ingredient search: %2.2f%%  done' %(100.0*(i+1-min)/(max-min)) )
            lastIng = ing
        if (i+1) % backUpCycle == 0:
            old_name = 'suppliersPCC.csv'
            base, extension = os.path.splitext('suppliersPCC.csv')
            new_name = os.path.join('Completed', base +'_'+str(lastBackUp+1)+'_'+str(i+1)+ extension)
            lastBackUp = i+1
            shutil.copy(old_name, new_name)
            print "Copied", old_name, "as", new_name
            #clear output
            #output.close()
            output = open('suppliersPCC.csv','w')
            supplierBackUp = open('supBackUp.txt','w')
            supplierBackUp.write(str(suppliers_infos_url)) 
            print 'back up made'

        #print ing
    #print suppliers_infos_url
    print len(suppliers_infos_url)
except Exception as e:
    output.close()
    driver.close()
    print e


print 'Ingredient search done'
retrieve_suppliers()
s = open('suppliers_last_ing.csv','w')
for key in suppliers_infos_url.keys():
    s.write(key+','+re.sub(',', ' ',suppliers_infos_url[key], flags=re.IGNORECASE)+'\n')
print 'Manufacturers infos search done'

output.close()
driver.close()
