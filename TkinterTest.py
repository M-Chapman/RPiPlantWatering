import tkinter

GUI = tkinter.Tk()

GUI.title('Raspberry Pi Plant Watering System')
B = tkinter.Button(GUI, bg = 'grey', text='This is a Button')

B.pack()

GUI.geometry("800x600")

GUI.mainloop()