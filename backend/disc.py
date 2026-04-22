import os

base_images  = set(os.listdir("base-model/dataset/Images"))
cord_images  = set(os.listdir("main-model/stage_1_cordseg/cord-dataset/images"))

print("In cord but not base:", cord_images - base_images)
print("In base but not cord:", base_images - cord_images)
print("####################################################")
print("Base images:", len(base_images))
print("Cord images:", len(cord_images))