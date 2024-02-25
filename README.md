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

## Setting up evaluations

To specify which categories you want to evaluate images by, you have to create a `schema.json` file
using `schema-template.json` as an example. Inside the json you see two keys:
`Categories` and `Evals`. They both mean evaluation categories: a criteria by which you evaluate the
image. But the difference between them is that with images `Categories` key are separated into
different directories, and both `Categories` and `Evals` evaluations are stored in the databank.
You can specify any `string` evaluation category you want as long as it's unique in the schema.
Each evaluation category key has an `int` value meaning the range of marks you'll have for that
specific evaluation. `Photographic: 5` Would mean you can range images by this category with marks 
from 1 to 5. 

The order of keys in `Categories` determines the directory structure. Everything that's higher in
the list is also higher in directory structure.
With the following `Categories` list:

cat1: 2,
cat2: 2,
cat3: 2

You will get the following directory structures for different sets of evaluations:

cat1/cat2/cat3
cat1/cat3/
cat1/
cat2/cat3/
cat2/
cat3/
