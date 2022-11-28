import nbd

from itertools import zip_longest
def string_layer_padder(iterable, n, fillvalue=None):
    "grouper(3, 'ABCDEFG', 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)

h =  nbd.NBD()
h.connect_uri("nbd://localhost:2007")

jw_string = """Meet Skrillex in Phoenix
Study zymurgy
Get a pet axolotl named Hexxus
Observe a syzygy from Zzyzx, California
Port the games Zzyzzyxx and Xexyz to Xbox
Publish a Zzzax/Mister Mxyzptlk crossover
Bike from Xhafzotaj, Albania to Qazaxbəyli, Azerbaijan
Paint an Archaeopteryx fighting a Muzquizopteryx
Finish a game of Scrabble without getting punched
Make something called xkcd"""

jw_string = "Тень, знай своё место"
jw_string = "XYZZY"
jw_string = "Klaatu barada nikto"
jw_string = "Oo ee oo ah ah ting tang walla walla bing bang"
jw_string = "By the Power of Grayskull, I HAVE THE POWER!!"

jw_string = """
"Jabberwocky"

'Twas brillig, and the slithy toves
Did gyre and gimble in the wabe;
All mimsy were the borogoves,
And the mome raths outgrabe.

"Beware the Jabberwock, my son!
The jaws that bite, the claws that catch!
Beware the Jubjub bird, and shun
The frumious Bandersnatch!"

He took his vorpal sword in hand:
Long time the manxome foe he sought-
So rested he by the Tumtum tree,
And stood awhile in thought.

And as in uffish thought he stood,
The Jabberwock, with eyes of flame,
Came whiffling through the tulgey wood,
And burbled as it came!

One, two! One, two! And through and through
The vorpal blade went snicker-snack!
He left it dead, and with its head
He went galumphing back.

"And hast thou slain the Jabberwock?
Come to my arms, my beamish boy!
O frabjous day! Callooh! Callay!"
He chortled in his joy.

'Twas brillig, and the slithy toves
Did gyre and gimble in the wabe;
All mimsy were the borogoves,
And the mome raths outgrabe.

from Through the Looking-Glass, and
What Alice Found There (1871)
""".strip()

jw_string = """He-man and the Masters of The Universe
I am Adam, Prince of Eternia, Defender of the secrets of Castle Grayskull.
This is Cringer, my fearless friend.
Fabulous secret powers were revealed to me the day I held aloft my magic sword and said "By the Power of Grayskull, I HAVE THE POWER!!"
Cringer became the mighty BattleCat and I became He-man, the most powerful man in the universe.
Only three others share this secret: our friends the Sorceress, Man-At-Arms and Orko. Together we defend Castle Grayskull from the evil forces of Skeletor."""

jw_string = """~We're no strangers to love
You know the rules and so do I (do I)
A full commitment's what I'm thinking of
You wouldn't get this from any other guy
I just wanna tell you how I'm feeling
Gotta make you understand
Never gonna give you up
Never gonna let you down
Never gonna run around and desert you
Never gonna make you cry
Never gonna say goodbye
Never gonna tell a lie and hurt you
We've known each other for so long
Your heart's been aching, but you're too shy to say it (say it)
Inside, we both know what's been going on (going on)
We know the game and we're gonna play it
And if you ask me how I'm feeling
Don't tell me you're too blind to see
Never gonna give you up
Never gonna let you down
Never gonna run around and desert you
Never gonna make you cry
Never gonna say goodbye
Never gonna tell a lie and hurt you
Never gonna give you up
Never gonna let you down
Never gonna run around and desert you
Never gonna make you cry
Never gonna say goodbye
Never gonna tell a lie and hurt you
We've known each other for so long
Your heart's been aching, but you're too shy to say it (to say it)
Inside, we both know what's been going on (going on)
We know the game and we're gonna play it
I just wanna tell you how I'm feeling
Gotta make you understand
Never gonna give you up
Never gonna let you down
Never gonna run around and desert you
Never gonna make you cry
Never gonna say goodbye
Never gonna tell a lie and hurt you
Never gonna give you up
Never gonna let you down
Never gonna run around and desert you
Never gonna make you cry
Never gonna say goodbye
Never gonna tell a lie and hurt you
Never gonna give you up
Never gonna let you down
Never gonna run around and desert you
Never gonna make you cry
Never gonna say goodbye
Never gonna tell a lie and hurt you"""

BLOCKSIZE = 32 #ctx.block_size(handle)[1] # preferred block size

jw_string = jw_string.encode('UTF-8')

#for i, v in enumerate(string_layer_padder(jw_string, BLOCKSIZE, 0)):
#	h.pwrite(bytearray(v), BLOCKSIZE*i)
h.pwrite(bytearray(2048), 0)
h.pwrite(jw_string, 0)

string_bytes = b""
for ptr in range(0, len(jw_string), BLOCKSIZE):
	read_buffer = h.pread(BLOCKSIZE, ptr)
	print(read_buffer)

	if b"\x00" in read_buffer:
		string_bytes += read_buffer[:read_buffer.index(b"\x00")]
		break
	else:
		string_bytes += read_buffer

if string_bytes != jw_string:
	print(string_bytes)
	print(jw_string)
else:
	print(":+1:")