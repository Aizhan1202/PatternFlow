import tensorflow as tf
import matplotlib.pyplot as plt

model = tf.keras.models.load_model("model.ckpt")

n = 5
plt.tight_layout()
fig, axs = plt.subplots(n, 2, figsize=(256,256))
for i in range(n):
    noise = tf.random.uniform(shape=(1,32,32,8))
    noise2 = tf.random.uniform(shape=(1,32,32,8))
    axs[i,0].imshow(tf.reshape(model.decoder.predict(model.vq.predict(noise)), shape=(256,256)))
    axs[i,1].imshow(tf.reshape(model.decoder.predict(model.vq.predict(noise2)), shape=(256,256)))
plt.savefig("out.png", dpi=50)
