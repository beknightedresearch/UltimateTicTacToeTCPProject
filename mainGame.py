'''
Created on Mar 27, 2019

@author: Sarah McCarty
I used Python 3.7.0 with VS Code and Eclipse on my Windows PC
'''
import select, socket, sys, queue
from datetime import *
from random import randint
import math
import threading
import time
from pathlib import Path

'''
printBoard: prints the board in human-readable form
board: board in array form to be printed
'''
def printBoard(board):
    sideLength=int(math.sqrt(len(board)))
    print(" ",end="")
    for i in range(sideLength):
        if(i%3==0):
            print(" ", end="")
        if(i<10):
            print(" ",end="")
        print(" "+str(i),end="")
    print()
    for j in range(sideLength):
        if(j%3==0):
            for k in range(sideLength*3+int(sideLength/3)+2):
                print("-", end="")
            print()
        if(j<10):
            print(" ",end="")
        print(str(j),end="")
        for i in range(sideLength):
            if(i%3==0):
                print("-", end="")
            l=board[j*sideLength+i]
            if(l=="B"):
                print("|"+" "+"|",end="")
            else:
                print("|"+l+"|", end="")
        print()
'''
valid27: determines whether a cordinate of a move is valid on a 27x27 board
t: the overall coordinate (may be x or y coordinate)
lT: the corresponding coordinate of the last move
'''
def valid27(t,lT):
    if(int(lT) not in range(27)):
        return False
    valid1=False
    valid2=False
    if((lT%3==0 and t in [0,1,2,9,10,11,18,19,20])):
        valid1=True
    elif(lT%3==1 and t in [3,4,5,12,13,14,21,22,23]):
        valid1=True
    elif(lT%3==2 and t in [6,7,8,15,16,17,24,25,26]):
        valid1=True
    if(lT%9 in range(3) and t in range(9)):
        valid2=True
    elif(lT%9 in range(3,6) and t in range(9,18)):
        valid2=True
    elif(lT%9 in range(6,9) and t in range(18,27)):
        valid2=True
    return valid1 and valid2
'''
isWinning3: Checks if a 3x3 board has been won
board: the board in array form to check
t: the letter of player to check if has won
'''
def isWinning3(board,t):
    win=False
    combos=[(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(6,4,2)]
    for k1,k2,k3 in combos:
        if(board[k1]==t and board[k2]==t and board[k3]==t):
            win=True
            break
    return win
'''
isValidMove: Checks if a move is valid based upon the last move
row: row coordinate of move
col: column coordinate of move
lastMove: tuple of last move coordinate
size: size of board
'''
def isValidMove(row,col,lastMove,size):
    if(row>int(size)-1 or col>int(size)-1 or row<0 or col <0):
        #checks if valid coordinates for board size at all
        return False
    lR=int(lastMove[0])
    lC=int(lastMove[1])
    if(lR not in range(int(size)) or lC not in range(int(size))):
        #if last move is not in range, then this is the first move
        return True
    if(int(size)==3):
        #anywhere on the board is valid for a 3x3
        return True
    if(int(size)==9):
        if(lC%3*3<=col and col<lC%3*3+3 and lR%3*3<=row and row <lR%3*3+3):
            return True
        else:
            return False
    if(int(size)==27):
        #checks if both the x and y coordinate are valid
        return valid27(row,lR) and valid27(col,lC)
'''
    checkWin: checks if a player is winning the board
    s: socket of game to check
    last_move: the last move as a tuple
    game_board: the game board
    size: size of board
    medium_zoom_board: dictionary of medium zoom boards
    large_zoom_board: dictionary of large zoom boards
    charToCheck: letter of player to check if they have won
    competitor: screenname of competitor

    the entire dictionaries are passed to simplify updating their values
    (because dictionaries are passed by reference)
'''
def checkWin(s,last_move,game_board,size,\
     medium_zoom_board, large_zoom_board, charToCheck,\
          competitor):
    if(size==3):
        if(isWinning3(game_board,charToCheck)):
            print(competitor+" has won the game!")
            print("You can continue playing if you would like, otherwise use endGame")
    if(size==9):
        smallBoard=findSmallBoard(game_board,last_move[0]//3,last_move[1]//3)
        if(isWinning3(smallBoard,charToCheck)):
            medium_zoom_board[s][(last_move[0]//3)*3+last_move[1]//3]=charToCheck
            if(isWinning3(medium_zoom_board[s],charToCheck)):
                print(competitor+" has won the game!")
                print("You can continue playing if you would like, otherwise use endGame")
    if(size==27):
        smallBoard=findSmallBoard(game_board,last_move[0]//3,last_move[1]//3)
        if(isWinning3(smallBoard,charToCheck)):
            medium_zoom_board[s][(last_move[0]//3)*9+last_move[1]//3]=charToCheck
            smallMedZoomBoard=findSmallBoard(medium_zoom_board[s],last_move[0]//9,last_move[1]//9)
            if(isWinning3(smallMedZoomBoard,charToCheck)):
                large_zoom_board[s][(last_move[0]//9)*3+last_move[1]//9]=charToCheck
                if(isWinning3(large_zoom_board[s],charToCheck)):
                    print(competitor+" has won the game!")
                    print("You can continue playing if you would like, otherwise use endGame")          

'''
    boardToString: Converts board array to string form
    board: board to convert
'''
def boardToString(board):
    strB=""
    for i in range(len(board)-1):
        strB=strB+board[i]+","
    strB=strB+board[len(board)-1]
    return strB
'''
    keyboardListening: thread to listen for commands from the user
    threadcount: number of threads
    q: queue to push new commands to
    readyForCommands: Event flag of whether to prompt for more commands
'''
def keyboardListening(threadcount,q, readyForCommands):
    ArgumentLength={"makeMove":2,"seeBoard":0,"switchGame":1,"acceptGame":1,"pickLetter":1,"gameList":0,"undo":0,"acceptUndo":0,"denyUndo":0,"endGame":0,"newGame":4,"seeIP":0,"help":0,"currentGame":0,"rules":0,"loadGame":5,"saveGame":1,"openPort":1,"closePort":1,"portsList":0}
    while True:
        readyForCommands.wait()
        #has to wait for output of other things to be printed out
        command = input("Input command: ")
        splitOut=command.split()
        if(len(splitOut)==0):
            print("Invalid command")
        elif(splitOut[0] in ["makeMove","seeBoard","switchGame","acceptGame","pickLetter","gameList","undo","acceptUndo","denyUndo","endGame","sendMessage","newGame","seeIP","currentGame","help","rules","loadGame","saveGame","openPort","closePort","portsList"]):
            valid=False
            if(splitOut[0]=="sendMessage"):
                valid=True
            elif(len(splitOut)-1==ArgumentLength[splitOut[0]]):
                valid=True
            if(valid):
                q.put(command)
                readyForCommands.clear()
                #wait for other thread to finish handling these commands
            else:
                print("Invalid number of arguments")
        else:
            print("Invalid command")
'''
    findSmallBoard: returns the little board (3x3) associated with a row and col of a big board
    board: board the small board is located
    row: row coordinate of box in small board
    col: col coordinate of box in small board
'''
def findSmallBoard(board,row,col):
    littleBoard=[]
    for l in range(3):
        for m in range(3):
            littleBoard.append(board[(l+3*row)*3+m+3*col])
    return littleBoard

"""
    removeSocketFromEverything: When communication terminates with a socket,
    it needs to be removed from all of the data structures.
"""
def removeSocketFromEverything(sckt, inputs, outputs, message_queues, servers, game_boards, undo_boards,\
    board_size,game_indexes, indexes_to_game,competitors,your_character,your_move,second_last_move,last_move,\
        medium_zoom_board,large_zoom_board,your_undo_requests,their_undo_requests, readable,writable,exceptional):
        if sckt in inputs:
            inputs.remove(sckt)
        if sckt in outputs:
            outputs.remove(sckt)
        if sckt in readable:
            readable.remove(sckt)
        if sckt in writable:
            writable.remove(sckt)
        if sckt in exceptional:
            exceptional.remove(sckt)
        if sckt in servers.values():
            del servers[sckt.getsockname()[1]]

        sckt.close()
        try:
            del message_queues[sckt]
            del indexes_to_game[game_indexes[sckt]]
            del your_move[sckt]
            del second_last_move[sckt]
            del last_move[sckt]
            del your_character[sckt]
            del game_boards[sckt]
            del undo_boards[sckt]
            del game_indexes[sckt]
            del board_size[sckt]
            del competitors[sckt]
            try:
                #smaller boards will not have zoom boards
                del medium_zoom_board[sckt]
                del large_zoom_board[sckt]
            except KeyError:
                pass
            if sckt in your_undo_requests:
                your_undo_requests.remove(sckt)
            if sckt in their_undo_requests:
                their_undo_requests.remove(sckt)
        except KeyError:
            print("There was an error removing the socket")
            pass
        

"""
    handleCommands: Responsible for handling commands by the user
    Data structures the same as from socketListening
"""
def handleCommands(activeGame, inputs, outputs, message_queues, serverSocks, servers, game_boards, undo_boards,\
    board_size,game_indexes, indexes_to_game,competitors,your_character,your_move,second_last_move,last_move,\
        medium_zoom_board,large_zoom_board,your_undo_requests,their_undo_requests, readable,writable,exceptional,\
            emptyBoards, q, currentIndex):
    while(not q.empty()):
        try:
            next_command = q.get_nowait()
        except queue.Empty:
            pass
        else:
            splitOut=next_command.split()
            print("")
            if(len(splitOut)==0):
                print("Invalid command")
            elif(splitOut[0]=="makeMove"):
                noErrorsFlag=True
                if(activeGame is not None and activeGame in writable):
                    if(your_move[activeGame]):
                        if(activeGame not in their_undo_requests):
                            #users must addres undo requests before playing
                            try:
                                rowlength=int(board_size[activeGame])
                                row = int(splitOut[1])
                                column = int(splitOut[2])
                            except ValueError:
                                print("Invalid argument.")
                                noErrorsFlag=False
                            board=game_boards[activeGame]
                            if(isValidMove(row,column,last_move[activeGame],board_size[activeGame]) and noErrorsFlag):
                                #if valid move update all of the data structures and send to opponent
                                undo_boards[activeGame]=game_boards[activeGame].copy()
                                board[row*rowlength+column]=your_character[activeGame]
                                game_boards[activeGame]=board
                                your_move[activeGame]=False
                                second_last_move[activeGame]=last_move[activeGame].copy()
                                last_move[activeGame]=[row,column]
                                msg="MM\n"+str(row)+","+str(column)+"\n"+boardToString(game_boards[activeGame])
                                activeGame.send(msg.encode())
                                print("The current board is now: ")
                                printBoard(game_boards[activeGame])

                                #Check to see if this move has caused you to win the game
                                charToCheck=your_character[activeGame]
                                size=int(board_size[activeGame])
                                checkWin(activeGame,last_move[activeGame],game_boards[activeGame],size,\
                                    medium_zoom_board,large_zoom_board,charToCheck,\
                                        competitors[activeGame])                            
                            else:
                                print("Invalid move")
                        else:
                            print("Your opponent has made a request to undo. Accept or reject this request before playing.")
                    else:
                        print("It is not your turn on this game.")
                else:
                    print("There is not an active game, use switchGame to choose one or newGame to start one.")
            elif(splitOut[0]=="seeBoard"):
                if(activeGame is not None):
                    printBoard(game_boards[activeGame])
                else:
                    print("There is not an active game, use switchGame to choose one or newGame to start one.")
            elif(splitOut[0]=="switchGame"):
                try:
                    activeGame=indexes_to_game[int(splitOut[1])]
                except ValueError:
                    print("Invalid argument")
                except KeyError:
                    print("Invalid argument")
                print("The active game has switched to index "+splitOut[1]+" with "+competitors[activeGame])
            elif(splitOut[0]=="acceptGame"):
                if(activeGame is not None and activeGame in writable):
                    if(your_character[activeGame] not in ["X","O"]):
                        #randomly pick who goes first
                        first=randint(0,1)
                        if(first==1):
                            print(competitors[activeGame]+" will go first. Use pickLetter command to pick your choice of letter.")
                            your_character[activeGame]="U"
                            #to indicate it is the user's choice                               
                        else:
                            print("You will go first. Your opponent is picking their letter.")
                    else:
                        #this occurs after a loaded game. your_move had already been set.
                        if(your_move[activeGame]):
                            print("You will go next. Use makeMove to make your choice")
                            first=0
                        else:
                            print("Your opponent will go next.")
                            first=1
                        printBoard(game_boards[activeGame])
                    msg="AG\n"+str(first)+"\n"+splitOut[1]
                    activeGame.send(msg.encode())
                else:
                    print("There is not an active game, use switchGame to choose one or newGame to start one.")
            elif(splitOut[0]=="pickLetter"):
                if(activeGame is not None and activeGame in writable):
                    if(splitOut[1] in ["X","O"]):
                        if(activeGame in your_character.keys() and your_character[activeGame]=="U"):
                            #letter U is set by acceptGame to indicate who gets to pick their letter
                            your_character[activeGame]=splitOut[1]
                            msg="PL\n"+splitOut[1]
                            activeGame.send(msg.encode())
                        else:
                            print("You cannot pick the letter now.")
                    else:
                        print("Invalid character. Must be X or O")
                else:
                    print("There is not an active game, use switchGame to choose one or newGame to start one.")
            elif(splitOut[0]=="gameList"):
                print("Your current games are:")
                for key in competitors.keys():
                    print(str(game_indexes[key])+": "+competitors[key])
            elif(splitOut[0]=="undo"):
                if(activeGame is not None and activeGame in writable):
                    if(your_move[activeGame]):
                        print("Your opponent has already gone. It is too late to undo.")
                    elif(not undo_boards[activeGame]):
                        print("You and your opponent have already undone your last move.")
                    else:
                        your_undo_requests.add(activeGame)
                        msg="UR\n"
                        activeGame.send(msg.encode())
                else:
                    print("There is not an active game, use switchGame to choose one or newGame to start one.")
            elif(splitOut[0]=="acceptUndo"):
                if(activeGame is not None and activeGame in writable):
                    #if an undo is accepted everything is reverted to back-up
                    #only 1 level of history is kept, so two sequential undos
                    #cannot be performed
                    game_boards[activeGame]=undo_boards[activeGame]
                    undo_boards[activeGame]=[]
                    last_move[activeGame]=second_last_move[activeGame].copy()
                    second_last_move[activeGame]=[]
                    your_move[activeGame]=False
                    their_undo_requests.remove(activeGame)
                    msg="UA\n"
                    activeGame.send(msg.encode())
                else:
                    print("There is not an active game, use switchGame to choose one or newGame to start one.")
            elif(splitOut[0]=="denyUndo"):
                if(activeGame is not None and activeGame in writable):
                    their_undo_requests.remove(activeGame)
                    msg="UD\n"
                    activeGame.send(msg.encode())
                else:
                    print("There is not an active game, use switchGame to choose one or newGame to start one.")
            elif(splitOut[0]=="endGame"):
                if(activeGame is not None and activeGame in writable):
                    msg="EG\n"
                    activeGame.send(msg.encode())
                    #delete the socket from all of the data structures
                    removeSocketFromEverything(activeGame, inputs, outputs, message_queues, servers, game_boards, undo_boards,\
                        board_size,game_indexes, indexes_to_game,competitors,your_character,your_move,second_last_move,last_move,\
                            medium_zoom_board,large_zoom_board,your_undo_requests,their_undo_requests, readable,writable,exceptional)
                else:
                    print("There is not an active game, use switchGame to choose one or newGame to start one.")
            elif(splitOut[0]=="sendMessage" and activeGame in writable):
                if(activeGame is not None):
                    #the message is the whole command minus the sendMessage space
                    msg="SC\n"+splitOut[1]
                    activeGame.send(msg.encode())
                else:
                    print("There is not an active game, use switchGame to choose one or newGame to start one.")
            elif(splitOut[0]=="openPort"):
                try:
                    if int(splitOut[1]) in range(1024,65337):
                        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        server.setblocking(0)
                        server.bind(('localhost', int(splitOut[1])))
                        server.listen(5)
                        serverSocks.put((server,int(splitOut[1])))
                        print("Port has been opened.")
                    else:
                        print("Invalid port number. Must be between 1024 and 65336.")
                except OSError:
                    print("There was an error. Try using a different port.")
            elif(splitOut[0]=="closePort"):
                if int(splitOut[1]) in servers.keys():
                    sckt = servers[int(splitOut[1])]
                    removeSocketFromEverything(sckt, inputs, outputs, message_queues, servers, game_boards, undo_boards,\
                            board_size,game_indexes, indexes_to_game,competitors,your_character,your_move,second_last_move,last_move,\
                                medium_zoom_board,large_zoom_board,your_undo_requests,their_undo_requests, readable,writable,exceptional)
                    print("Port has been closed.")
                else:
                    print("There is not a socket associated with that port number.")
            elif(splitOut[0]=="portsList"):
                print("Your open ports are:")
                for port in servers.keys():
                    print(port)
            elif(splitOut[0]=="newGame"):
                noErrorsFlag = True
                try:
                    clientSocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                    clientSocket.connect((splitOut[1],int(splitOut[2])))
                    commandMsg = "OG\n"+splitOut[3]+"\n"+splitOut[4]
                    clientSocket.send(commandMsg.encode())
                except ValueError:
                    print("There was an error creating the socket. Check your arguments.")
                    noErrorsFlag=False
                except ConnectionRefusedError:
                    print("The connection was refused. Check your arguments")
                    noErrorsFlag=False
                if(noErrorsFlag):
                    message_queues[clientSocket] = queue.Queue()
                    activeGame=clientSocket
                    inputs.append(activeGame)
                    competitors[activeGame]="Waiting for Response"
                    your_character[activeGame]="B"
                    #to indicate that is yet to be picked
                    game_indexes[activeGame]=currentIndex
                    indexes_to_game[currentIndex]=activeGame
                    board_size[activeGame]=splitOut[3]
                    currentIndex=currentIndex+1
                    game_boards[activeGame]=emptyBoards[splitOut[3]].copy()
                    #only larger boards have zoom boards
                    if(splitOut[3]=="9"):
                        medium_zoom_board[activeGame]=emptyBoards["3"].copy()
                    if(splitOut[3]=="27"):
                        medium_zoom_board[activeGame]=emptyBoards["9"].copy()
                        large_zoom_board[activeGame]=emptyBoards["3"].copy()
                    undo_boards[activeGame]=[]
                    your_move[activeGame]=False
                    last_move[activeGame]=[-1,-1]
                    second_last_move[activeGame]=[]
            elif(splitOut[0]=="loadGame"):
                noErrorsFlag=True
                try:
                    clientSocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                    clientSocket.connect((splitOut[1],int(splitOut[2])))
                except ConnectionRefusedError:
                    print("Connection refused. Check IP and port number.")
                    noErrorsFlag=False
                except ValueError:
                    print("Invalid command. Check your arguments.")
                    noErrorsFlag=False
                if(noErrorsFlag):
                    try:
                        f=open(Path(splitOut[3]),"r")
                        CharBoard=f.read()
                        char = CharBoard.split()[0]
                        last = CharBoard.split()[1]
                        lastMove = CharBoard.split()[2]
                        board = CharBoard.split()[3]
                    except IOError:
                        print("Invalid File")
                        noErrorsFlag=False
                    except KeyError:
                        print("Invalid File")
                        noErrorsFlag=False
                    except IndexError:
                        print("Invalid File")
                        noErrorsFlag=False
                    if(char=="X"):
                        #the character sent will be the character of the receiver instead of us
                        commandMsg = "LG "+splitOut[4]+" O "+board+" "+splitOut[5]+" "+str(last)+" "+lastMove+" "+CharBoard.split()[4]+" "+CharBoard.split()[5]
                    elif(char=="O"):
                        commandMsg="LG "+splitOut[4]+" X "+board+" "+splitOut[5]+" "+str(last)+" "+lastMove+" "+CharBoard.split()[4]+" "+CharBoard.split()[5]
                    else:
                        print("Invalid File")
                        noErrorsFlag=False
                if(noErrorsFlag):
                    boardAsArray=board.split(",")
                    clientSocket.send(commandMsg.encode())
                    message_queues[clientSocket] = queue.Queue()
                    activeGame=clientSocket
                    inputs.append(activeGame)
                    competitors[activeGame]="Waiting for Response"
                    your_character[activeGame]=char
                    game_indexes[activeGame]=currentIndex
                    indexes_to_game[currentIndex]=activeGame
                    board_size[activeGame]=str(int(math.sqrt(len(boardAsArray))))
                    currentIndex=currentIndex+1
                    game_boards[activeGame]=boardAsArray
                    undo_boards[activeGame]=[]
                    if(board_size[activeGame]=="9"):
                        medium_zoom_board[activeGame]=CharBoard.split()[4].split(",")
                    if(board_size[activeGame]=="27"):
                        medium_zoom_board[activeGame]=CharBoard.split()[4].split(",")
                        large_zoom_board[activeGame]=CharBoard.split()[5].split(",")
                    if(last=="1"):
                        your_move[activeGame]=False
                    else:
                        your_move[activeGame]=True
                    last_move[activeGame]=lastMove.split(",")
                    second_last_move[activeGame]=[]
            elif(splitOut[0]=="saveGame"):
                location=splitOut[1]
                board=game_boards[activeGame]
                print(board)
                try:
                    f=open(Path(location),"w")
                    print(your_character[activeGame]+" ",file=f,end="")
                    if(your_move[activeGame]):
                        last=0
                    else:
                        last=1
                    print(str(last)+" ",file=f,end="")
                    print(str(last_move[activeGame][0])+","+str(last_move[activeGame][1])+" ",file=f,end="")
                    for i in range(len(board)):
                        print(board[i]+",", file=f, end="")
                    print(" ", file=f,end="")
                    if activeGame in medium_zoom_board.keys():
                        for i in range(len(medium_zoom_board[activeGame])):
                            print(medium_zoom_board[activeGame][i]+",",file=f,end="")
                    else:
                        print("B",file=f,end="")
                    print(" ",file=f,end="")
                    if activeGame in large_zoom_board.keys():
                        for i in range(len(large_zoom_board[activeGame])):
                            print(large_zoom_board[activeGame][i]+",",file=f,end="")
                    else:
                        print("B",file=f,end="")
                    f.close()
                except IOError:
                    print("There was an error saving the game.")
                print("The game was saved. ")
            elif(splitOut[0]=="seeIP"):
                if(activeGame is not None and activeGame in writable):
                    print(activeGame.getpeername())
                else:
                    print("There is not an active game, use switchGame to choose one or newGame to start one.")
            elif(splitOut[0]=="currentGame"):
                if(activeGame is not None):
                    print("The competitor is "+competitors[activeGame]+" with index "+str(game_indexes[activeGame]))
                else:
                    print("There is not an active game, use switchGame to choose one or newGame to start one.")
            elif(splitOut[0]=="help"):
                f=open(Path('userCommandsDocumentation.txt'),'r')
                for line in f:
                    print(line)
            elif(splitOut[0]=="rules"):
                f=open(Path('rules.txt'),'r')
                for line in f:
                    print(line)
            else:
                print("Invalid command: "+splitOut[0])
    return activeGame, currentIndex

"""
   handleData: Responsible for handling all incoming messages from the sockets
   Data structures the same as from socketListening

"""
def handleData(command, data, s,activeGame, inputs, outputs, message_queues, servers, game_boards, undo_boards,\
    board_size,game_indexes, indexes_to_game,competitors,your_character,your_move,second_last_move,last_move,\
        medium_zoom_board,large_zoom_board,your_undo_requests,their_undo_requests, readable,writable,exceptional,\
            emptyBoards, currentIndex):
    print("")
    if(command=="OG"):
        bSize=data.splitlines()[0]
        competitor=data.splitlines()[1]
        print(competitor+" invites you to play Ultimate Tic-Tac-Toe with a "+bSize+"x"+bSize+" board")
        print("This game is now the active game and has index: "+str(currentIndex))
        print("Use command acceptGame [your screenname] to accept")
        game_indexes[s]=currentIndex
        indexes_to_game[currentIndex]=s
        competitors[s]=competitor
        board_size[s]=bSize
        currentIndex=currentIndex+1
        your_character[s]="B"
        game_boards[s]=emptyBoards[bSize].copy()
        if(bSize=="9"):
            medium_zoom_board[s]=emptyBoards["3"].copy()
        if(bSize=="27"):
            medium_zoom_board[s]=emptyBoards["9"].copy()
            large_zoom_board[s]=emptyBoards["3"].copy()
        undo_boards[s]=[]
        your_move[s]=False
        last_move[s]=[-1,-1]
        second_last_move[s]=[]
        activeGame=s
    elif(command=="LG"):
        competitor=data.splitlines()[0]
        char=data.splitlines()[1]
        board=data.splitlines()[2]
        first=data.splitlines()[4]
        lastMove=data.splitlines()[5]
        medium_zoom_board[s]=data.splitlines()[6].split(",")
        large_zoom_board[s]=data.splitlines()[7].split(",")
        print(competitor+" invites you to play Ultimate Tic-Tac-Toe with a saved board called "+data.splitlines()[3])
        print("This game is now the active game and has index: "+str(currentIndex))
        print("You are "+char+".")
        print("Use command acceptGame [your screenname] to accept")
        game_indexes[s]=currentIndex
        indexes_to_game[currentIndex]=s
        competitors[s]=competitor
        board_size[s]=int(math.sqrt(len(board.split(","))))
        currentIndex=currentIndex+1
        your_character[s]=char
        game_boards[s]=board.split(",")
        undo_boards[s]=[]
        if(first=="0"):
            your_move[s]=False
        else:
            your_move[s]=True
        last_move[s]=lastMove.split(",")
        second_last_move[s]=[]
        activeGame=s
    elif(command=="AG"):
        competitors[s]=data.splitlines()[1]
        print(competitors[s]+" has accepted your game (index "+str(game_indexes[s])+").")
        if(your_character[s] not in ["X","O"]):
            if(data.splitlines()[0]=="1"):
                print(competitors[s]+" will choose their letter, and then you will go first")
                your_move[s]=False
                #because opponent needs to pick their letter first
            elif(data.splitlines()[0]=="0"):
                print(competitors[s]+" will go first.")
                print("Choose which letter you would like to be (X or O) with pickLetter command")
                your_character[s]="U"
                #to indicate it is their turn to pick the letter
                your_move[s]=False
        else:
            #this is a loaded game
            #your_move has already been set with loadGame
            if(your_move[s]):
                print("It's your turn, you are "+your_character[s]+". Use makeMove to resume the game")
                printBoard(game_boards[s])

            else:
                print("It's your opponent turn. You are "+your_character[s]+".")
                printBoard(game_boards[s])
        activeGame=s
    elif(command=="PL"):
        if(data=="X"):
            print("Your character will be O in game with "+competitors[s]+" (index "+str(game_indexes[s])+"). Use makeMove to start the game.")
            your_character[s]="O"
        else:
            print("Your character will be X in game with "+competitors[s]+" (index "+str(game_indexes[s])+"). Use makeMove to start the game.")
            your_character[s]="X"
        your_move[s]=True
        print("This is the empty board: ")
        printBoard(game_boards[s])
        activeGame=s
    elif(command=="EG"):
        print(competitors[s]+" has ended your game (index "+str(game_indexes[s])+").")
        print("Please choose a new active game using command switchGame [index]") 
        s.close()
        removeSocketFromEverything(s, inputs, outputs, message_queues, servers, game_boards, undo_boards,\
            board_size,game_indexes, indexes_to_game,competitors,your_character,your_move,second_last_move,last_move,\
                medium_zoom_board,large_zoom_board,your_undo_requests,their_undo_requests, readable,writable,exceptional)
    elif(command=="UR"):
        print(competitors[s]+" has requested to undo their last move. (index "+str(game_indexes[s])+")")  
        print("Accept or reject this request with acceptUndo or denyUndo")     
        activeGame=s
        their_undo_requests.add(s)
    elif(command=="UA"):
        your_undo_requests.remove(s)
        print("Your request for an undo has been granted. (index "+str(game_indexes[s])+").")
        print("It is your move with the following board:")
        game_boards[s]=undo_boards[s]
        undo_boards[s]=[]
        last_move[s]=second_last_move[s]
        second_last_move[s]=[]
        printBoard(game_boards[s])
        your_move[s]=True 
        activeGame=s
    elif(command=="UD"):
        your_undo_requests.remove(s)
        print("Your request for an undo has been denied. (index "+str(game_indexes[s])+").")
        print("It is still "+competitors[s]+"'s turn.")
        activeGame=s
    elif(command=="SC"):
        print(competitors[s]+" has sent the following message. (index "+str(game_indexes[s])+").")
        print(data) 
        print("You can reply using command sendMessage [message]")
        activeGame=s
    elif(command=="MM"):
        print(competitors[s]+" has picked "+data.splitlines()[0]+" (index "+str(game_indexes[s])+").")
        print("It is your turn with the following board: ")
        last_move[s]=[int(data.splitlines()[0].split(",")[0]),int(data.splitlines()[0].split(",")[1])]
        undo_boards[s]=game_boards[s].copy()
        game_boards[s]=data.splitlines()[1].split(",")
        size=int(math.sqrt(len(game_boards[s])))
        if(your_character[s]=="X"):
            charToCheck="Y"
        else:
            charToCheck="X"
        checkWin(s,last_move[s],game_boards[s],size,\
            medium_zoom_board,large_zoom_board,charToCheck,\
                competitors[s])
        printBoard(game_boards[s])
        activeGame=s
        your_move[s]=True                                 
    return activeGame, currentIndex

"""
socketListening: Responsible for listening for incoming communciations and executing commands

threadcount: iterable required for Threads
q: Queue which keyboardListening adds outstanding commands to and this thread processes
serverSocks: The queue of new server sockets to create
readyForCommands: Event flag to prevent the keyboard listening thread from trying
    to read commands while the app is printing out information
"""
def socketListening(threadcount,q,serverSocks, readyForCommands):
    """
        Data structures:
        inputs, outputs: lists of all sockets
        message_queues: queue of incoming data
        game_boards: Dictionary with sockets as keys and list as values. The lists are a 1D representation of
            the current game state
        undo_boards: Dictionary with sockets as keys and list as values. The lists are a 1D represenation of
            previous game state in case user request an undo
        board_size: Dictionary with sockets as keys and strings as value. The string is either "3", "9", "27"
            representng the size of the game board.
        game_indexes: Dictionary with sockets as keys and integers as values. The integer provides users
            a short-hand for referring to simulatenous games. Prevents issues with identical IPs or usernames.
        indexes_to_game: Dictionary with integers as keys and sockets as values. Provides reverse look-up for 
            game_indexes. Used when switching games.
        competitors: Dictionary with sockets as keys and strings as values. Strings are usernames of competitors.
        your_character: Dictionary with sockets as keys with chars as values. Char is "X" or "O" to represent player.
        your_move: Dictionary with sockets as keys and booleans as values on whether it is your turn.
        second_last_move: Dictionary with sockets as keys and integer pair as value
            with second last move (row,col) to validate new move after an undo.
        last_move: Dictionary with sockets as keys and integer pairs as value of last move (row,col) to validate
            next move.
        medium_zoom_board: Dictionary with sockets as keys and string lists as values. Indicates who has
            won 1 level removed boards in order to efficiently determine if anyone has won.
        large_zoom_board: Dictionary with sockets as keys and string lists as values. Indicates who has
            won 2 levels removed boards in order to efficiently determine if anyone has won.
        your_undo_requests: Set of sockets which have outstanding requests to undo by you.
        their_undo_requests: Set of sockets which have outsatnding request to undo by opponent.
        currentIndex: Indexes so far assigned to sockets.
        activeGame: Socket which is currently "active" the one which command will be applied to.
        empty3, empty9, empty27: Constants of new board of each of the 3 sizes
        emptyBoards: Dictionary of new board choices
        readable,writable,exceptional: back-up empty arrays when the select statement fails because 
            no sockets have been opened yet
    """
    inputs=[]
    outputs=[]
    servers={}
    message_queues={}
    game_boards={}
    undo_boards={}
    board_size={}
    game_indexes={}
    indexes_to_game={}
    competitors={}
    your_character={}
    your_move={}
    second_last_move={}
    last_move={}
    medium_zoom_board={}
    large_zoom_board={}
    your_undo_requests=set()
    their_undo_requests=set()
    currentIndex=1
    activeGame=None
    empty3=["B","B","B","B","B","B","B","B","B"]
    empty9=[]
    empty27=[]
    readable=[]
    writable=[]
    exceptional=[]
    #generate empty board (since they are large)
    for i in range(27*27):
        empty27.append("B")
    for i in range(81):
        empty9.append("B")
    emptyBoards={"3":empty3,"9":empty9,"27":empty27}
    #inputs.append(server)
    while True:
        while (not serverSocks.empty()):
            nextSock, port = serverSocks.get_nowait()
            inputs.append(nextSock)
            servers[port]=nextSock
        try:
            readable, writable, exceptional = select.select(
                inputs, outputs, inputs, 0.5)
            #timeout is used to ensure new commands are responded to
        except OSError:
            #select statement errors out on Windows if both inputs and outputs
            #are empty.
            readable=[]
            writable=[]
            exceptional=[]

        
        #Before returning to the sockets, go through outstanding commands
        readyForCommands.clear()
        activeGame, currentIndex=handleCommands(activeGame, inputs, outputs, message_queues, serverSocks, servers, game_boards, undo_boards,\
            board_size,game_indexes, indexes_to_game,competitors,your_character,your_move,second_last_move,last_move,\
                medium_zoom_board,large_zoom_board,your_undo_requests,their_undo_requests, readable,writable,exceptional,\
                    emptyBoards, q, currentIndex)
        for s in readable:
            if s in servers.values():
                #accept all connection requests
                connection, client_address = s.accept()
                connection.setblocking(0)
                inputs.append(connection)
                message_queues[connection] = queue.Queue()
            else:
                try:
                    data = s.recv(4096) 
                    if data:
                        try:
                            message_queues[s].put(data)
                            if s not in outputs:
                                outputs.append(s)
                        except KeyError:
                            print("There was an error with the socket")
                except ConnectionResetError:
                    removeSocketFromEverything(s, inputs, outputs, message_queues, servers, game_boards, undo_boards,\
                        board_size,game_indexes, indexes_to_game,competitors,your_character,your_move,second_last_move,last_move,\
                            medium_zoom_board,large_zoom_board,your_undo_requests,their_undo_requests, readable,writable,exceptional)
                    print("The connection was forcibly closed.")
                    #print("Input command: ")
        for s in writable:
            #before processing more incoming commands, do all outstanding outgoing commands
            try:
                next_msg = message_queues[s].get_nowait()
            except queue.Empty:
                pass
            else:
                next_msg=next_msg.decode()
                command = next_msg.splitlines()[0]
                data = next_msg[len(command)+1:]
                readyForCommands.clear()
                activeGame, currentIndex=handleData(command, data, s, activeGame, inputs, outputs, message_queues, servers, game_boards, undo_boards,\
                    board_size,game_indexes, indexes_to_game,competitors,your_character,your_move,second_last_move,last_move,\
                        medium_zoom_board,large_zoom_board,your_undo_requests,their_undo_requests, readable,writable,exceptional,\
                            emptyBoards, currentIndex)
                print("Input command: ")        
        readyForCommands.set()
        #the app is now ready for more incoming commands
        for s in exceptional:
            inputs.remove(s)
            if s in outputs:
                outputs.remove(s)
            s.close()
            removeSocketFromEverything(s, inputs, outputs, message_queues, servers, game_boards, undo_boards,\
                board_size,game_indexes, indexes_to_game,competitors,your_character,your_move,second_last_move,last_move,\
                    medium_zoom_board,large_zoom_board,your_undo_requests,their_undo_requests, readable,writable,exceptional)

print("Welcome to Ultimate Tic-Tac-Toe")
listeningport=0
threadcount=0
print("You are ready to start playing Ultimate Tic-Tac-Toe")
print("For help and list of commands, use the command help. For rules, use the command rules.")
commandsQueue = queue.Queue()
serverSocks = queue.Queue()
# a thread is created and started
threadcount=1
readyForCommands = threading.Event()
readyForCommands.set()
t1 =threading.Thread(target=keyboardListening, args=(threadcount,commandsQueue, readyForCommands)) 
t1.daemon=False
t1.start()
threadcount=2
t2 = threading.Thread(target=socketListening,args=(threadcount,commandsQueue,serverSocks,readyForCommands))
t2.start()


        

