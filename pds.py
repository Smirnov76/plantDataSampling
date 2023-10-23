import os
import shutil
from tkinter import *
from tkinter import ttk
from tkinter import filedialog as fd
from tkinter import scrolledtext
from tkinter.messagebox import showinfo
#import tkinter as tk
from PIL import ImageTk, Image
from datetime import date
from generateData import genData
import imghdr

class App(Tk):

    image_folder = ""
    images = []
    area_images_folder = "temp/"
    area_images = []
    viewed_images = []
    count_images = 0
    count_samples = []

    def selectFolder(self):
        self.image_folder = fd.askdirectory(initialdir=os.path.abspath(os.getcwd()))
        self.images = os.listdir(self.image_folder)

        for file in self.images:
            if not imghdr.what(os.path.join(self.image_folder, file)):
                self.images.remove(file)

        self.info.config(state=NORMAL)
        self.info.delete("1.0", END)
        self.info_text = f"Выбранная папка: {self.image_folder}\nВсего изображений: {len(self.images)}\n"
        self.info.insert(INSERT, self.info_text)
        self.highlightWord(["Выбранная папка", "Всего изображений"], self.info_text, "blue")
        self.info.config(state=DISABLED)

        self.cnt_train.config(text=f"Обучение: {self.ratio.get()}%")
        self.cnt_test.config(text=f"Тест: {self.ratio.get()}%")
        self.parts.config(state=ACTIVE)

        self.geometry("360x500")
        self.btn_start_sampling.config(state=ACTIVE)
        self.middle_frame.pack(side=TOP, padx=5, pady=2, fill=BOTH)

    def setRatio(self, val):
        train = str(self.ratio.get())
        self.cnt_train.config(text=f"Обучение: {train}%")
        test = str(100 - self.ratio.get())
        self.cnt_test.config(text=f"Тест: {test}%")

    def sampling(self):
        self.parts.config(state=DISABLED)
        self.btn_start_sampling.config(state=DISABLED)

        selected_size = self.select_sample_size.get()
        sample_size = 0
        if selected_size != "Свой":
            sample_size = int(f"{selected_size[0]}{selected_size[1]}")
        else:
            sample_size = int(f"{self.other_size.get()[0]}{self.other_size.get()[1]}")

        current_date = date.today()
        dataset_name = f"dataset-{self.ratio.get()}-{100-self.ratio.get()}-{sample_size}-{current_date}"
        train_p_dir = os.path.join(dataset_name, "train", "plant")
        test_p_dir = os.path.join(dataset_name, "test", "plant")
        train_b_dir = os.path.join(dataset_name, "train", "back")
        test_b_dir = os.path.join(dataset_name, "test", "back")


        gd = genData(self.image_folder, self.images, train_p_dir, test_p_dir, train_b_dir, test_b_dir,
                     float(self.ratio.get()/100), sample_size, self.flip_H.get(), self.flip_V.get())
        self.count_samples = gd.run()

        self.area_images = os.listdir(self.area_images_folder)
        for i, img_name in enumerate(self.images):
            self.result_preview.insert("", END, iid=str(i), text=img_name, values=[img_name])
            for aimg in self.area_images:
                if img_name.split('.')[0] in aimg:
                    self.result_preview.insert(str(i), END, text=aimg, values=[aimg])

        self.geometry("360x750")
        self.bottom_frame.pack(side=BOTTOM, padx=5, pady=3, fill=BOTH)
        self.info_text += f"Выбранное соотношение: {self.ratio.get()}%(обучение) / {100-self.ratio.get()}%(тест)\n" \
                          f"Выбранный размер семпла: {sample_size}\n\n"
        self.info_text += f"Всего семплов обучения для plant: {self.count_samples[0]}\n" \
                          f"Всего семплов теста для plant: {self.count_samples[1]}\n" \
                          f"Всего семплов обучения для back: {self.count_samples[2]}\n" \
                          f"Всего семплов теста для back: {self.count_samples[3]}"
        self.info.config(state=NORMAL)
        self.info.delete("1.0", END)
        self.info.insert(INSERT, self.info_text)
        self.highlightWord(["Выбранная папка", "Всего изображений", "Выбранное соотношение", "Выбранный размер семпла"],
                           self.info_text, "blue")
        self.info.config(state=DISABLED)

    def viewImage(self, event):
        selected_item = self.result_preview.focus()
        item_details = self.result_preview.item(selected_item)

        image = Image.open(f"{self.area_images_folder}{item_details.get('values')[0]}")
        width, height = image.size
        self.tk_image = ImageTk.PhotoImage(image.resize((int(width/2), int(height/2))))
        if self.tk_image not in self.viewed_images:
            self.viewed_images.append(self.tk_image)

        image_viewer = Toplevel(self)
        image_viewer.title(item_details.get('values')[0])
        image_viewer.geometry(f"{int(width/2)+10}x{int(height/2)}")
        canvas = Canvas(image_viewer)
        index = self.viewed_images.index(self.tk_image)
        canvas.create_image(0, 0, anchor=NW, image=self.viewed_images[index])
        canvas.pack(padx=5, pady=5, expand=True, fill=BOTH)

    def finishApp(self):
        if os.path.exists(self.area_images_folder) and self.confirm_del.get():
            shutil.rmtree(self.area_images_folder)
        self.destroy()

    def highlightWord(self, words, text, color):
        for l, line in enumerate(text.split("\n")):
            for word in words:
                if word in line:
                    start_index = line.index(word)
                    end_index = start_index + len(word)
                    self.info.tag_add("highlight", f"{l+1}.{start_index}", f"{l+1}.{end_index}")
        self.info.tag_config("highlight", foreground=color)

    def selectSize(self, event):
        if self.select_sample_size.get() == "Свой":
            self.other_size.config(state=NORMAL)
        else:
            self.other_size.config(state=DISABLED)

    def selectFlip(self):
        if self.flip_H.get() or self.flip_V.get():
            self.flip_none.set(0)

    def cancelFlip(self):
        if self.flip_none.get():
            self.flip_H.set(0)
            self.flip_V.set(0)

    def openInfo(self):
        message = "Федеральное государственное бюджетное учреждение науки Институт программных " \
                  "систем им. А.К. Айламазяна Российской академии наук (ИПС им. А.К. Айламазяна РАН)\n\n" \
                  "Лаборатория методов обработки и анализа изображений (ЛМОАИ)\n\n" \
                  "2023 год"
        showinfo(title="Разработчик", message=message)

    def __init__(self):
        super().__init__()
        self.title("PAS")
        self.geometry("360x200")
        self.update()
        self.protocol("WM_DELETE_WINDOW", self.finishApp)

        self.main_menu = Menu()
        self.select_folder_menu = Menu(tearoff=0)
        self.select_folder_menu.add_command(label="Выбрать папку", command=self.selectFolder)
        self.info_menu = Menu(tearoff=0)
        self.info_menu.add_command(label="Разработчик", command=self.openInfo)
        self.main_menu.add_cascade(label="Открыть", menu=self.select_folder_menu)
        self.main_menu.add_cascade(label="О программе", menu=self.info_menu)
        self.config(menu=self.main_menu)

        self.top_frame = LabelFrame(self, text="Инфо", borderwidth=1, relief=SOLID)#, padding=[5, 5])
        self.middle_frame = LabelFrame(self, text="Настройки выборки", borderwidth=1, relief=SOLID)
        self.bottom_frame = LabelFrame(self, text="Предпросмотр результата", borderwidth=1, relief=SOLID)

        self.info_text = "Select images folder by click on Open and Select folder"
        self.info_text = "Выберете папку с изображениями с помощью меню: Открыть -> Выбрать папку"
        self.info = scrolledtext.ScrolledText(self.top_frame, wrap=WORD, height=10, state=NORMAL)
        self.info.insert(INSERT, self.info_text)
        self.highlightWord(["Открыть", "Выбрать папку"], self.info_text, "blue")
        self.info.config(state=DISABLED)

        self.frame = Frame(self.middle_frame)
        self.sampling_info = Label(self.frame, text="Выберете размер элемента выборки(семпла)")
        sample_sizes = ["32x32", "64x64", "Свой"]
        self.select_sample_size = ttk.Combobox(self.frame, values=sample_sizes, state="readonly", width=6)
        self.select_sample_size.set(sample_sizes[0])
        self.select_sample_size.bind("<<ComboboxSelected>>", self.selectSize)
        self.other_size = Entry(self.frame, width=10, state=DISABLED)

        self.sampling_info2 = Label(self.middle_frame, text="Выберете соотношение обучение/тест")
        self.ratio = IntVar(value=50)
        self.parts = ttk.Scale(self.middle_frame, orient=HORIZONTAL, length=100, from_=0, to=100, variable=self.ratio,
                               command=self.setRatio, state=DISABLED)
        self.cnt_train = ttk.Label(self.middle_frame, text="Обучение")
        self.cnt_test = ttk.Label(self.middle_frame, text="Тест")

        self.flips_frame = Frame(self.middle_frame)
        self.flips_info = Label(self.flips_frame, text="Выберете метод отражения семпла")
        flips = ["Отразить по горизонтали",
                 "Отразить по вертикали",
                 "Без отражения"]
        self.flip_H = IntVar()
        self.flip_check_H = ttk.Checkbutton(self.flips_frame, text=flips[0], variable=self.flip_H,
                                            onvalue=1, offvalue=0, command=self.selectFlip)
        self.flip_V = IntVar()
        self.flip_check_V = ttk.Checkbutton(self.flips_frame, text=flips[1], variable=self.flip_V,
                                            onvalue=1, offvalue=0, command=self.selectFlip)
        self.flip_none = IntVar()
        self.flip_none.set(1)
        self.flip_check_none = ttk.Checkbutton(self.flips_frame, text=flips[2], variable=self.flip_none,
                                               onvalue=1, offvalue=0, command=self.cancelFlip)

        self.btn_start_sampling = ttk.Button(self.middle_frame, text="Генерация выборки", width=55,
                                             command=self.sampling, state=DISABLED)

        self.confirm_del = IntVar(value=1)
        self.check_del = ttk.Checkbutton(self.bottom_frame, text="Удалить изображения зон выборки",
                                         variable=self.confirm_del, onvalue=1, offvalue=0)

        self.result_preview = ttk.Treeview(self.bottom_frame, show="tree", height=400)
        self.myscrollbar = Scrollbar(self.bottom_frame, orient="vertical", command=self.result_preview.yview)
        self.result_preview.configure(yscrollcommand=self.myscrollbar.set)
        self.result_preview.bind("<Double-Button-1>", self.viewImage)

        self.top_frame.pack(side=TOP, padx=5, pady=2, fill=BOTH)
        self.info.pack(padx=5, pady=5, fill=X)
        self.frame.pack(anchor=NW, fill=BOTH)
        self.sampling_info.pack(side=TOP, anchor=NW, padx=10, pady=(5, 1))
        self.select_sample_size.pack(side=LEFT, padx=(27, 3), pady=5)
        self.flips_frame.pack(side=TOP, anchor=NW)
        self.flips_info.pack(side=TOP, anchor=NW, padx=10, pady=(5, 1))
        self.flip_check_H.pack(anchor=NW, padx=25)
        self.flip_check_V.pack(anchor=NW, padx=25)
        self.flip_check_none.pack(anchor=NW, padx=25)
        self.other_size.pack(side=LEFT, padx=3, pady=5)
        self.sampling_info2.pack(side=TOP, anchor=NW, padx=10, pady=(5, 1))
        self.parts.pack(padx=5, pady=5, fill=X)
        self.btn_start_sampling.pack(padx=5, pady=5, side=BOTTOM)
        self.cnt_train.pack(padx=5, pady=5, side=LEFT)
        self.cnt_test.pack(padx=5, pady=5, side=RIGHT)
        self.check_del.pack(padx=5, anchor=NW, fill=X)
        self.myscrollbar.pack(side=RIGHT, fill=Y)
        self.result_preview.pack(padx=5, pady=5, expand=True, fill=BOTH)


if __name__ == "__main__":
    app = App()
    app.mainloop()