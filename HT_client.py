import xmlrpc.client
import socket

#Client socket to connect to server socket
ClientMultiSocket = socket.socket()
host = 'localhost'
port = 9000
print('Waiting for connection response')
try:
    #Connect to server
    ClientMultiSocket.connect((host, port))
except socket.error as e:
    print(str(e))
#Check message from server
res = ClientMultiSocket.recv(2048)
while True:
    #Create server proxy in order to communicate with server
    #Source for all rpc client functionality: https://docs.python.org/3/library/xmlrpc.server.html#module-xmlrpc.server
    with xmlrpc.client.ServerProxy("http://localhost:8000") as proxy:
        #Get user input for first and last page
        Input = input("Give starting page: ")
        Input2 = input("Give final page: ")
        #Send to add function
        all_links, route_size = proxy.add(Input,Input2)
        #Print results
        print("The final page is at a distance of " + str(route_size)+ "link from the final page")
        print("The following pages contain links to the final page: ")
        for i in all_links:
            print(i)
        #Check if user wants to end using the server
        Input0 = input("Do you want to end run (Y/N):")
        if(Input0 == "Y"):
            break
#Close socket
ClientMultiSocket.close()
