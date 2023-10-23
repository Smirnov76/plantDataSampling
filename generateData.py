import cv2 as cv
import numpy as np
import os
import random

class genData:
    def __init__(self, image_dir, images, ps_train_folder, ps_test_folder, bs_train_folder, bs_test_folder, ratio,
                 sample_size, flip_h, flip_v):
        self.image_dir = image_dir
        self.images = images
        self.ps_train_folder = ps_train_folder
        self.ps_test_folder = ps_test_folder
        self.bs_train_folder = bs_train_folder
        self.bs_test_folder = bs_test_folder
        self.ratio = ratio
        self.fh = flip_h
        self.fv = flip_v

        os.makedirs(self.ps_train_folder, exist_ok=True)
        os.makedirs(self.ps_test_folder, exist_ok=True)
        os.makedirs(self.bs_train_folder, exist_ok=True)
        os.makedirs(self.bs_test_folder, exist_ok=True)

        self.ps_train_cnt = 0
        self.ps_test_cnt = 0
        self.bs_train_cnt = 0
        self.bs_test_cnt = 0
        self.box_size = sample_size

        os.makedirs("temp", exist_ok=True)
        self.area_images = []

    def FindContours(self, input_image, min_area, output_image):
        contours, hierarchy = cv.findContours(input_image, cv.RETR_LIST, cv.CHAIN_APPROX_SIMPLE)

        contours_select = []
        for cnt in contours:
            min_area = cv.contourArea(cnt)
            if (min_area > 2000):
                contours_select.append(cnt)

        cv.drawContours(output_image, contours_select, -1, 255, thickness=cv.FILLED)
        return output_image, contours_select


    def CollectSampleRects(self, select_contours, image_mask, box_size, threshold_perc):
        threshold = (box_size * box_size * threshold_perc) / 100
        sample_rects = []
        for cnt in select_contours:
            x, y, w, h = cv.boundingRect(cnt)
            for j in range(x, x + w, box_size):
                for k in range(y, y + h, box_size):
                    roi = image_mask[k:k + box_size, j:j + box_size]
                    cont = cv.countNonZero(roi)
                    if (cont > threshold):
                        # cv.rectangle(img, (j, k), (j + box_w, k + box_h), (0, 255, 0), 1)
                        rect = [j, k, j + box_size, k + box_size]
                        sample_rects.append(rect)

        return sample_rects

    def SaveSamplesFromImg(self, samples_folder, samples_array, image, cnt_all, color, area_img_name, fh, fv):
        colors = {
            "green": (0, 255, 0),
            "blue": (255, 0, 0),
            "red": (0, 0, 255),
            "yellow": (0, 255, 255)
        }
        area_img = np.zeros((image.shape[0], image.shape[1], 3), dtype=np.uint8)
        for i, s in enumerate(samples_array):
            sample = image[s[1]:s[3], s[0]:s[2]]
            cv.rectangle(area_img, (samples_array[i][0], samples_array[i][1]), (samples_array[i][2],
                                                                                samples_array[i][3]), colors[color], -1)
            name_sample = os.path.join(samples_folder, f"{i + 1 + cnt_all}.jpg")
            cv.imwrite(name_sample, sample)
            if fh:
                name_sample = os.path.join(samples_folder, f"{i + 1 + cnt_all + len(samples_array) * fh}.jpg")
                sample_fh = cv.flip(sample, 1)
                cv.imwrite(name_sample, sample_fh)
            if fv:
                name_sample = os.path.join(samples_folder, f"{i + 1 + cnt_all + len(samples_array) * (fh + 1)}.jpg")
                sample_fv = cv.flip(sample, 0)
                cv.imwrite(name_sample, sample_fv)
        area_img = cv.addWeighted(image, 0.5, area_img, 0.5, 0.0)
        cv.imwrite(area_img_name, area_img)


    def run(self):
        print("START GENERATE DATASET")
        print(f"Directory for TRAIN PLANT samples: {self.ps_train_folder}")
        print(f"Directory for TEST  PLANT samples: {self.ps_test_folder}")
        print(f"Directory for TRAIN BACK samples: {self.bs_train_folder}")
        print(f"Directory for TEST  BACK samples: {self.bs_test_folder}")
        print("---------------------")

        for image in self.images:
            self.area_images.append(f"temp/{image.split('.')[0]}_plant_train_area.jpg")
            self.area_images.append(f"temp/{image.split('.')[0]}_plant_test_area.jpg")
            self.area_images.append(f"temp/{image.split('.')[0]}_back_train_area.jpg")
            self.area_images.append(f"temp/{image.split('.')[0]}_back_test_area.jpg")

            img = cv.imread(os.path.join(self.image_dir, image))
            img_copy = img.copy()
            img = cv.GaussianBlur(img, (9, 9), 0)
            lab = cv.cvtColor(img, cv.COLOR_BGR2Lab)
            l, a, b = cv.split(lab)

            ret, otsu_bin_a = cv.threshold(a, 0, 255, cv.THRESH_BINARY_INV + cv.THRESH_OTSU)
            # ret,otsu_bin_b = cv.threshold(b,0,255,cv.THRESH_BINARY+cv.THRESH_OTSU)
            ret, otsu_bin_b = cv.threshold(b, 145, 255, cv.THRESH_BINARY)
            bitwise_ab = cv.bitwise_or(otsu_bin_a, otsu_bin_b)
            bitwise_not_ab = cv.bitwise_not(bitwise_ab)

            height, width, channels = img.shape
            plant_mask = np.zeros((height, width, 1), np.uint8)
            plant_mask, contours_select_plant = self.FindContours(bitwise_ab.copy(), 2000, plant_mask)

            background_mask = np.zeros((height, width, 1), np.uint8)
            background_mask, contours_select_back = self.FindContours(bitwise_not_ab.copy(), 2000, background_mask)

            print(f"for image: {image}")

            plant_sample_rects = self.CollectSampleRects(contours_select_plant, plant_mask, self.box_size, 80) #75
            print(f"- count plant samples: {len(plant_sample_rects)}")

            random.shuffle(plant_sample_rects)
            plant_train = plant_sample_rects[:int((len(plant_sample_rects) + 1) * self.ratio)]
            plant_test = plant_sample_rects[int((len(plant_sample_rects) + 1) * self.ratio):]
            print(f"-- count train samples: {len(plant_train)}")
            print(f"-- count test  samples: {len(plant_test)}")

            self.SaveSamplesFromImg(self.ps_train_folder, plant_train, img_copy, self.ps_train_cnt, "green",
                                    self.area_images[0], self.fh, self.fv)
            #self.ps_train_cnt += len(plant_train)
            self.ps_train_cnt = len(os.listdir(self.ps_train_folder))
            self.SaveSamplesFromImg(self.ps_test_folder, plant_test, img_copy, self.ps_test_cnt, "blue",
                                    self.area_images[1], self.fh, self.fv)
            #self.ps_test_cnt += len(plant_test)
            self.ps_test_cnt = len(os.listdir(self.ps_test_folder))

            back_sample_rects = self.CollectSampleRects(contours_select_back, background_mask, self.box_size, 80) #60
            print(f"- cont back samples: {len(back_sample_rects)}")

            random.shuffle(back_sample_rects)
            back_train = back_sample_rects[:int((len(back_sample_rects) + 1) * self.ratio)]
            back_test = back_sample_rects[int((len(back_sample_rects) + 1) * self.ratio):]
            print(f"-- count train samples: {len(back_train)}")
            print(f"-- count test  samples: {len(back_test)}")

            self.SaveSamplesFromImg(self.bs_train_folder, back_train, img_copy, self.bs_train_cnt, "red",
                                    self.area_images[2], self.fh, self.fv)
            #self.bs_train_cnt += len(back_train)
            self.bs_train_cnt = len(os.listdir(self.bs_train_folder))
            self.SaveSamplesFromImg(self.bs_test_folder, back_test, img_copy, self.bs_test_cnt, "yellow",
                                    self.area_images[3], self.fh, self.fv)
            #self.bs_test_cnt += len(back_test)
            self.bs_test_cnt = len(os.listdir(self.bs_test_folder))

            self.area_images.clear()

        print(f"Total TRAIN samples for PLANT: {self.ps_train_cnt}")
        print(f"Total  TEST samples for PLANT: {self.ps_test_cnt}")
        print(f"Total TRAIN samples for  BACK: {self.bs_train_cnt}")
        print(f"Total  TEST samples for  BACK: {self.bs_test_cnt}")

        return [self.ps_train_cnt, self.ps_test_cnt, self.bs_train_cnt, self.bs_test_cnt]
