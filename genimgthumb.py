import genimg

genimg.generate_image(
    outfile="thumbnail.png",
    prompt=" A sleek and modern logo design for a gaming startup, featuring a stylized geometric phoenix icon with sharp, angular wings. The color scheme is a gradient of vibrant purle transitioning to deep red, The typography is clean and sans-serif, with the company name placed below the icon in bold, uppercase letters. The overall style is minimalistic, with (flat design principles) , emphasizing symmetry, clean lines, and a sense of dynamic motion. Designed for versatility across digital and print mediums.",
    model="OfficialStableDiffusion/dreamshaper_8LCM",
    seed=-1,
    steps=5,
    cfgscale=2.0,
    aspectratio="1:1",
    width=512,
    height=512,
    sampler="lcm",
    automaticvae=True,
    images=1
)