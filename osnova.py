import pickle

Token = "5674020335:AAHEuAZju8w6oAa0gPn89P3f19GAMyX3Ojk"

state = {}
with open("data.dat", 'wb') as f:
    pickle.dump(state, f)




