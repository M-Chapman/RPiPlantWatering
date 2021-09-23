import tkinter as tk

GUI = tk.Tk()

frame = tk.Frame(GUI)
frame.pack()

def BTask():
    print("B has been pressed!")


GUI.title('Raspberry Pi Plant Watering System')
B = tk.Button(frame, fg = 'blue', text='This is a Button', command = BTask)

BBot = tk.Button(frame, fg='red', text = 'Button 2')

BBot.pack()
B.pack()

GUI.geometry("800x600")

def task():
    print('Hello World!')
    GUI.after(2000,task)

GUI.after(2000, task)

GUI.mainloop()