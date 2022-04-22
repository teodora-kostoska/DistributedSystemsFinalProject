from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
import socket
from _thread import *
import wikipediaapi
import concurrent.futures
import itertools
import re
from time import sleep

# Restrict to a particular path.
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)
#Source for multithreaded socket server functionality: https://www.positronx.io/create-socket-server-with-multiple-clients-in-python/
#Initialize socket
serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host = "localhost"
port = 9000
#Bind the socket to host and port
try:
    serverSocket.bind((host, port))
    print("Socket listening on port 9000...")
#Catch exceptions
except socket.error as e:
    print(str(e))
#Listen to up to 5 clients
serverSocket.listen(5)

#This is the main worker unit, in here the child threads are created
def task(page, last_page, route_size):
    #Source for all wikipedia api usage https://pypi.org/project/Wikipedia-API/
    #Connect to api
    wiki_wiki = wikipediaapi.Wikipedia('en')
    #Get the page
    page_py = wiki_wiki.page(page)
    #Get links on page
    links = page_py.links
    #This is for stopping the while loop
    continue_looking = True;
    #Keep track of links to pages that need to be checked
    all_links = []
    #Keep track of pages already checked
    all_data = []
    #Temporary list in order to only collect unique values into all_links
    all_links3 = []
    #Keep track of pages that contained the final page
    results = []
    #Clean the final page so that it can be compared to other pages link results
    clean_final = re.sub(r"[^a-zA-Z0-9 ]", "", last_page)
    #Go through the titles of every link in page
    for title in sorted(links.keys()):
        #Add to the list so that they can be used later to fetch pages
        all_links.append(title)
        #Clean the title also
        clean_title = re.sub(r"[^a-zA-Z0-9 ]", "", title)
        #Compare current title to the goal title, if it matches set continue_looking to False -> no loop or child units created
        if clean_final.strip().lower()== clean_title.strip().lower():
            print("Link to " + last_page + " on page " + page)
            continue_looking = False;
    #Loop for creating child units that will go through links
    while(continue_looking):
        #Create concurrent thread pool executor, which will create the child units and distribute links to child units
        #Sources for all threadPoolExecutro workings: https://www.tutorialspoint.com/concurrency_in_python/concurrency_in_python_pool_of_threads.htm
        #https://analyticsindiamag.com/how-to-run-python-code-concurrently-using-multithreading/
        with concurrent.futures.ThreadPoolExecutor(max_workers = 10) as executor:
            #Collect the returned values from task2
            returned = {executor.submit(task2, link, last_page, route_size): link for link in all_links}
            #Set the used data into all_data
            all_data = all_data + all_links
            #Empty all_links
            all_links = []
            #Go through futures as they complete
            for future in concurrent.futures.as_completed(returned):
                #Title of the current page
                title = returned[future]
                try:
                    #Get results
                    data, result, route_size,continue_looking2 = future.result()
                #Catch exceptions
                except Exception as exc:
                    print('%r generated an exception: %s' % (title, exc))
                    break;
                #Check whether continue_looking is true, if it is, then set the latest continue_looking value that was returned from task2 module
                if(continue_looking == True):
                    continue_looking = continue_looking2;
                #If result contains some value, append it to the list that will be returned to client
                if len(result) != 0:
                    results.append(result)
                #Go through all the values in data and create the next all_links list, which is a list of pages that need to be checked
                for value in data:
                    all_links.append(value)
            #If continue_looking got set to false, break out of the while loop
            if(continue_looking == False):
                break;
            #temporarily set all_links to all_links3
            all_links3 = all_links
            #Empty all_links
            all_links = []
            #Add to all_links only unique values
            #Code for checking for unique values: https://www.tutorialspoint.com/get-unique-values-from-a-list-in-python
            for value in all_links3:
                if value not in all_links:
                    all_links.append(value)
        #Shutdown any threads that are still executing
        executor.shutdown()
    #Return the results and the route_size
    return results, route_size

#Task2 that each child unit uses to go through the links in the page that it was allocated
def task2(page, last_page, route_size):
    #Create connection to api, get page and links in page
    wiki_wiki = wikipediaapi.Wikipedia('en')
    page_py = wiki_wiki.page(page)
    links = page_py.links
    #Increase route_size by one as now we are one page further than the given page
    route_size = route_size +1
    #Set continue_looking to true
    continue_looking = True
    #Keep track of all links on page
    all_links = []
    #Keep track of pages that contain link to wanted final page
    results = []
    #Clean final for checking if it is in any of the links on page
    clean_final = re.sub(r"[^a-zA-Z0-9 ]", "", last_page)
    #Go through titles of links on page
    for title in sorted(links.keys()):
        all_links.append(title)
        #Clean title of link on page
        clean_title = re.sub(r"[^a-zA-Z0-9 ]", "", title)
        #Check whether same as goal page
        if clean_final.strip().lower()== clean_title.strip().lower():
            #Add to results if same
            results.append(page)
            #Set continue_looking to false
            continue_looking = False
    #Wait 1 sec before returning, this so to reduce strain on wikipedia api
    sleep(1)
    #Return results
    return all_links, results, route_size, continue_looking
    
def adder_function(x, y):
    #Connection to wikipedia api
    wiki_wiki = wikipediaapi.Wikipedia('en')
    #Get page
    page_py = wiki_wiki.page(x)
    #Initialize all_links and route_size
    all_links = []
    route_size = 0
    #Check whether beginning page and final page exist, if they don't return that they don't exist
    if page_py.exists() != True:
        print("Page doesn't exist")
        all_links.append(x + " page doesn't exist")
        return all_links, route_size
    elif wiki_wiki.page(y).exists() != True:
        all_links.append(y + "page doesn't exits")
        return all_links, route_size
    #Call task in order to initialize child units
    all_links, route_size = task(x, y, route_size)
    #Return values that were returned from task
    return all_links, route_size

#Source for multi threading: https://www.positronx.io/create-socket-server-with-multiple-clients-in-python/
#Define function to create multiple threads
def multi_thread(connection):
    #Send to client that server ok
    connection.send(str.encode('Server is working:'))
    #Create the rpc server
    #Source for all rpc server functionality: https://docs.python.org/3/library/xmlrpc.server.html#module-xmlrpc.server
    with SimpleXMLRPCServer(('localhost', 8000),requestHandler=RequestHandler) as server:
        server.register_introspection_functions()
        print("Listening on port 8000...")
        #Register added_function to server
        server.register_function(adder_function, 'add')
        #Set server as slave
        try:
            server.serve_forever()
        #Catch keyboard interrupt exception
        except KeyboardInterrupt:
            print("\nKeyboard interrupt received, exiting.")
            sys.exit(0)
#List of clients
client_list = []
while True:
    #Collect the client info
    Client, address = serverSocket.accept()
    print('Connected to: ' + address[0] + ':' + str(address[1]))
    #Start new thread for client
    start_new_thread(multi_thread, (Client, ))
    client_list.append(Client)
#Close server socket
serverSocket.close()


