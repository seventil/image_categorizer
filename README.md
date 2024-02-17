# image_categorizer
## General description
I used to collect a lot of images as references for digital paintings and studies. One of the best 
ways that I found in studying images is comparing them using different attributes in mind.
It is also a great way to build up taste - compare two images, see what you like more, repeat many 
times - you'll build up strong preferences. Attributes may vary between people, but may be, for 
example: color, contrast, texture, etc. The more you get into it, the more sophisticated attributes 
you'll want to use.

Besides evaulation, you'll want categorize images with (maybe) different attributes
for each category. For example, one category is landscape with ratings on composition and color,
the other is anatomy with ratings on complexity. Some categories may be exclusive - that means
they'll get their separate folders. For example, ballet may be exlusive and include photographic,
anatomy nested categories.

On top of evaluations listed in a schema, images are evaluated on category scales as well.
Photography categry with concept subcategory may include evaulations on color and texture
which gives 4 evaulations total: photography, concept, color, texture.

## Project setup
prerequisites:
```bash
python3.12 -m venv ./venv/
source venv/bin/activate
pip3 install kivy
pip3 install pillow
```

to run:
```bash
python3 main.py
```

## Storing evaluation information
### json databank
Here is a view of how json databank describing images and their evaulations are stored compared to
how the actual images are stored. A, B, C... indexes stand to store no more than 1000 images in 
one folder and to differentiate between how they're evaluated. If no evaluation ranges are present 
yet, it's only two: 1/2. The higher the mark - the better the parameter. 

When working through
stored images it's important to do relative evaluations by comparison. If 1/2 is not enough and
you'd want something in between: 2 shifts to 3, and 2 becomes empty, now you can restructure 
1 into 1,2; 3 into 2,3 and after that compare whatever you have in 2 with each other with new shift 
3->4, 2->2,3.

For subcategories naming goes the following way: <category mark>_<subcategory mark>_<literal index>

- databank
    - category1 folder
        - 1_A.json
        - 1_B.json
        - 2_A.json
        - category1_1_subcategory1 folder
            - 1_1_A.json

### evaluated images storage
- outputs
    - category1 folder
        - 1_A folder
            - 1_A img1
            ...
            - 1_A img1000
        - 1_B folder
            - 1_B img1
            ...
            - 1_B img1000
        - 2_A folder
            - 2_A img1
            ...
            - 2_A img1000
        - category1_subcategory1 folder
            - 1_1_A folder
                - 1_1_A img1
                ...
                - 1_1_A img1000

