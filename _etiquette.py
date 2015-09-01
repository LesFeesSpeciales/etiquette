# TODO
# - cleanup parsing: avoid duplication for template/metadata modes
# - ffmpeg: check env, tmp dir, command


import bpy
import os, time, json
from pprint import pprint


### UTILS
def HTMLColorToRGB(colorstring):
    """ convert #RRGGBB to an (R, G, B) tuple, from http://code.activestate.com/recipes/266466-html-colors-tofrom-rgb-tuples/ """
    colorstring = colorstring.strip()
    if colorstring[0] == '#': colorstring = colorstring[1:]
    if len(colorstring) != 6:
        raise ValueError("input #%s is not in #RRGGBB format" % colorstring)
    r, g, b = colorstring[:2], colorstring[2:4], colorstring[4:]
    r, g, b = [int(n, 16)/255.0 for n in (r, g, b)]
    return (r, g, b)

def frames_to_timecode(frame, framerate=25):
    """from http://stackoverflow.com/questions/8488238/how-to-do-timecode-calculation"""
    return '{0:02d}:{1:02d}:{2:02d}:{3:02d}'.format(frame // (3600*framerate),
                                                    frame // (60*framerate) % 60,
                                                    frame // framerate % 60,
                                                    frame % framerate)

def get_name_pattern(name, token='#'):
    """Get a string's padding pattern"""
    
    l = ['']
    
    last_isdigit = name[0].isdigit()
    
    for c in name:
        if last_isdigit == c.isdigit():
            l[-1]+=c
        else:   
            l.append(c)
            
            last_isdigit = not last_isdigit
        
    
    for i in range(len(l)-1, -1, -1):
        if l[i][0].isdigit():
            l[i] = token #* len(l[i])
            break
    
    
    out = ''.join(l)
    return out

def get_frame_number(name, token='#'):
    """TODO: avoid duplicate function?"""
    
    l = ['']
    
    last_isdigit = name[0].isdigit()
    
    for c in name:
        if last_isdigit == c.isdigit():
            l[-1]+=c
        else:   
            l.append(c)
            
            last_isdigit = not last_isdigit

    for i in range(len(l)-1, -1, -1):
        if l[i][0].isdigit():
            return int(l[i])

    return 0
            
def padding(s, frame):
    """Get frame's final name from expression"""

#    if not '#' in s:
#        s += '{:04}'.format(frame)

    out = ''
    pad = 0
    for c in s + '_':
        if c != '#':
            
            if pad != 0:
                num = ('{:0' + str(pad) + '}').format(frame)
                out += num
            
                pad = 0
            out +=c
        else:
            pad += 1
    
    out = out[0:-1]
    if not '#' in os.path.basename(s):
        out = '{}{:04}'.format(out,frame)
    return out


#####


class Metadata:
    """Base Metadata class. Subclass to implement other types"""
    def __init__(self, parent_stamp, meta_dict, screen_position, channel):
        
        self.screen_position = screen_position

        # screen_position in
        # [
        #   'TOP-LEFT',    'TOP',    'TOP-RIGHT',
        #   'LEFT',        'CENTER', 'RIGHT',
        #   'BOTTOM-LEFT', 'BOTTOM', 'BOTTOM-RIGHT'
        # ]

        self.parent_stamp = parent_stamp
        # self.field = meta_dict['field']
        # self.value = meta_dict['value']
        # self.size  = meta_dict['size']
        # self.inline  = meta_dict['inline']
        # self.color = meta_dict['color']
        for k, v in meta_dict.items():
            setattr(self, k, v)

        if type(self.color) is str:
            self.color = HTMLColorToRGB(self.color)

        self.channel = channel

        if screen_position[0] == 0:
            self.align = 'LEFT'
        elif screen_position[0] == 1:
            self.align = 'CENTER'
        elif screen_position[0] == 2:
            self.align = 'RIGHT'

    def get_blender_position(self):
        x, y = 0.0, 0.0
        # iterate through all other meta, calculate their size and
        # add them if they're on the same quadrant, until we reach this one

        previous_meta = None
        for other_meta in self.parent_stamp.metadatas:

            if other_meta.screen_position == self.screen_position: #same quadrant
                if previous_meta is None:
                    if other_meta == self:
                        break
                    previous_meta = other_meta
                    continue

                if other_meta.inline:
                    x += previous_meta.size * (len(previous_meta.get_text(0)) + 2) * 3/5 / self.parent_stamp.resolution[0]
                else:
                    x = 0.0
                    y += previous_meta.size / self.parent_stamp.resolution[1]

                previous_meta = other_meta

                if previous_meta == self:
                    break

        # if not self.inline:
        # # else:
        #     x = 0.0
        #     y += other_meta.size / self.parent_stamp.resolution[1]

        if self.screen_position[0] == 1:
            x += 0.5 
        if self.screen_position[1] == 1:
            y += 0.5 

        if self.screen_position[0] == 2:
            x = 1.0 - x
        if self.screen_position[1] == 2:
            y = 1.0 - y - self.size / self.parent_stamp.resolution[1]


        return x,y

    def render(self):

        for f in range(*self.parent_stamp.frame_range):

            text = self.get_text(f)

            channel = 2

            self.add_text(self.parent_stamp.sequencer, text, self.get_blender_position(), self.size, channel, f, self.align, self.color)

    @staticmethod
    def add_text(sequencer, text, position, size, channel, frame, align, font_color=[1.0,1.0,1.0]):
        #TODO: BG
        #

        # deselect all
        for s in sequencer.sequences:
            s.select = False


        txt_seq = sequencer.sequences.new_effect('{}_f{:04}'.format(text, frame), 'TEXT', channel, frame, frame+1)
        txt_seq.text = text
        # txt_seq.blend_type = 'OVER_DROP'
        txt_seq.location = position
        txt_seq.align = align
        txt_seq.font_size = size


        col_seq = sequencer.sequences.new_effect('{}_f{:04}_col'.format(text, frame), 'COLOR', channel+1, frame, frame+1)
        col_seq.color = font_color
        col_seq.blend_type = 'MULTIPLY'
        # txt_seq.location = position

        bpy.ops.sequencer.meta_make()
        meta_strip = sequencer.active_strip
        meta_strip.blend_type = 'OVER_DROP'

    def get_text(self, frame):
        value = self.get_value(frame)

        text_format = self.format if hasattr(self, "format") else '{field} : {value}'

        text = text_format.format(field=self.field, value=value)
        return text

    def get_value(self, frame):
        return self.value
        # return '{} : {}'.format(self.field, self.value)

class Frame_Metadata(Metadata):
    def get_value(self, frame):
        return frame
        # return '{} : {:02}'.format(self.field, frame)

class Timecode_Metadata(Metadata):
    def get_value(self, frame):
        return frames_to_timecode(frame)
        # return '{} : {}'.format(self.field, frames_to_timecode(frame))

class Date_Metadata(Metadata):
    def get_value(self, frame):
        date = time.strftime("%d/%m/%Y") if self.value == 'today' else self.value
        # date = '{} : {}'.format(self.field, date)
        return date


class Render_stamp:
    def __init__(self, metadata, images_paths, render_dir, settings):
        # self.metadatas = [[[] for x in range(3)] for y in range(3)]
        self.metadatas = []
        self.settings = settings

        for m in metadata:
            self.insert(m)

        self.setup_sequencer(images_paths, render_dir)


        for m in self.metadatas:
            m.render()

        self.render()


    def setup_sequencer(self, images_paths, render_dir):

        scene = bpy.context.scene
        self.sequencer = scene.sequence_editor_create()

        # Get images using same pattern in dir
        if len(images_paths) == 1:
            imgs = []
            img_dir, img_name = os.path.split(images_paths[0])
            pattern = get_name_pattern(img_name)
            file_list = os.listdir(img_dir)
            for f in file_list:
                if get_name_pattern(f) == pattern:
                    imgs.append(os.path.join(img_dir, f))
            images_paths = imgs
            images_paths.sort(key=get_frame_number)

        
        scene.frame_start = get_frame_number(images_paths[0])
        scene.frame_end = get_frame_number(images_paths[-1])
        self.frame_range = (scene.frame_start, scene.frame_end+1)

        img_seq = self.sequencer.sequences.new_image('img', images_paths[0], 1, scene.frame_start)


        for i in images_paths[1:]:
            img_seq.elements.append(os.path.basename(i))


        # Scene options

        img_seq.update()
        scene.update()

        # Get image size
        img = bpy.data.images.load(images_paths[0])

        settings = self.settings

        output_width = settings["resolution"][0] if "resolution" in settings else img.size[0]
        output_height = settings["resolution"][1] if "resolution" in settings else img.size[1]

        scene.render.resolution_x = output_width
        scene.render.resolution_y = output_height
        self.resolution = output_width, output_height

        scene.render.resolution_percentage = 100
        
        if bpy.app.build_options.codec_ffmpeg:
            scene.render.image_settings.file_format = 'H264'
            scene.render.ffmpeg.format = 'QUICKTIME'

        scene.render.filepath = render_dir

    def insert(self, meta):
        position = meta['position'].split('-')
        if len(position) == 1:
            if position[0] in ['LEFT', 'RIGHT']:
                position.append('CENTER')
            if position[0] in ['TOP', 'BOTTOM']:
                position.insert(0, 'CENTER')
            if position[0] == 'CENTER':
                position.append('CENTER')

        if position[1]   == 'LEFT':
            x = 0
        elif position[1] == 'CENTER':
            x = 1
        elif position[1] == 'RIGHT':
            x = 2

        if position[0] == 'BOTTOM':
            y = 0
        elif position[0] == 'CENTER':
            y = 1
        elif position[0]   == 'TOP':
            y = 2

        channel = 2

        # is there a better way of doing this?

        if meta['field'] == 'Frame':
            meta_type = Frame_Metadata
        elif meta['field'] == 'Date':
            meta_type = Date_Metadata
        elif meta['field'] == 'Timecode':
            meta_type = Timecode_Metadata
        else:
            meta_type = Metadata

        self.metadatas.append(meta_type(self, meta, (x, y), channel))


    def render(self):
        bpy.ops.render.render(animation=True)


def main():
    """Parse arguments"""

    import sys       # to get command line args
    import argparse  # to parse options for us and print a nice help message

    # get the args passed to blender after "--", all of which are ignored by
    # blender so scripts may receive their own arguments
    argv = sys.argv

    if "--" not in argv:
        argv = []  # as if no args are passed
    else:
        argv = argv[argv.index("--") + 1:]  # get all args after "--"

    usage_text = \
    """Select images to add to sequence and arguments for metadata"""

    parser = argparse.ArgumentParser(description=usage_text, prog="python etiquette.py", epilog="-----"*3, conflict_handler='resolve', add_help=False)

    parser.add_argument("-o", "--out", dest="render_dir", metavar='PATH',
            help="Render sequence to the specified path")
    parser.add_argument("-t", "--template", help="Template file")
    parser.add_argument("-w", "--width", help="Output width", type=int)
    parser.add_argument("-h", "--height", help="Output width", type=int)

    parser.add_argument("-m", "--metadata", type=str,
help="""Metadata description. They are of the form:
field:"Author",value:"Me",position:TOP-LEFT,inline:True, size:15,color:[1,1,1]
You can specify multiple fields separated by semicolons.""")


    args, u_args = parser.parse_known_args(argv)

    ### parse metadata from template
    if args.template:
        with open(args.template, 'r') as f:
             template_args = f.read()
             template_args = (json.loads(template_args))

        template_metadata = template_args["metadata"]

        parser = argparse.ArgumentParser(description=usage_text, conflict_handler='resolve', epilog="-----"*3)

        parser.add_argument("-o", "--out", dest="render_dir", metavar='PATH',
                help="Render sequence to the specified path")
        parser.add_argument("-t", "--template", help="Template file")
        parser.add_argument("-w", "--width", help="Output width", type=int)
        parser.add_argument("-h", "--height", help="Output width", type=int)
        parser.add_argument("image", nargs='+', type=str, help="Path to an image")
        parser.add_argument("--default", help="Use all default values", action='store_true')


        for arg in template_metadata:
            
            # if the value in the template is null, the field is a flag (cf. store_true);
            # only special fields are options, as frame, timecode, date
            if arg["value"] is None:
                parser.add_argument('--{}'.format(arg["field"].lower()), dest=arg["field"].lower(),
                    help=arg["field"], action='store_true', default=None)
            
            # otherwise, it's an argument
            else:
                parser.add_argument('--{}'.format(arg["field"].lower()), dest=arg["field"].lower(),
                    help=arg["field"], nargs="?", const=arg["value"])

        args = parser.parse_args(argv)



        for arg in template_metadata[:]:

            arg_key = arg["field"].lower()
            if hasattr(args, arg_key):
                arg_value = getattr(args, arg_key)
                if arg_value is not None:
                    arg_index = template_metadata.index(arg)
                    template_metadata[arg_index]["value"] = arg_value
                elif not args.default:
                    template_metadata.remove(arg)

        print("\nTEMPLATE_ARGS")
        pprint(template_metadata)
        metadata = template_metadata

        settings = template_args["settings"]



    ### parse metadata from metadata string
    elif args.metadata:
        usage_text = \
    """Select images to add to sequence and arguments for metadata.
Special fields for metada:
    - date returns today's date by default.
    - frame returns the current frame
    - timecode returns the current timecode"""
        parser = argparse.ArgumentParser(description=usage_text, epilog="-----"*3, conflict_handler='resolve', formatter_class=argparse.RawTextHelpFormatter)

        parser.add_argument("-o", "--out", dest="render_dir", metavar='PATH',
                help="Render sequence to the specified path")
        parser.add_argument("-t", "--template", help="Template file")
        parser.add_argument("-w", "--width", help="Output width", type=int)
        parser.add_argument("-h", "--height", help="Output width", type=int)
        parser.add_argument("image", nargs='+', type=str, help="Path to an image")
        parser.add_argument("-m", "--metadata", type=str,
help="""Metadata description. They are of the form:
{"field":"Author","value":"Me","position":"TOP-LEFT","inline":true,"size":15,"color":[1,1,1]}
You can specify multiple fields inside the braces separated by semicolons.""")
        
        args = parser.parse_args(argv)

        _metadata = json.loads(args.metadata)
        metadata = []
        default_meta = {
            'position': 'BOTTOM-LEFT',
            'field': 'Field',
            'value': 'Value',
            'color': [0.0, 0.0, 0.0], 
            'size': 15,
            'inline': True
        }

        for m in _metadata:
            metadata.append(default_meta.copy())
            for k, v in m.items():
                metadata[-1][k] = v

        settings = {}
        
    else:
        parser.add_argument("image", nargs='+', type=str, help="Path to an image")
        parser.print_help()
        sys.exit()


    # Default resolution
    if not "resolution" in settings:
        settings["resolution"] = [1920,1080]
        
    # Output resolution from command line
    if hasattr(args, "width") and args.width is not None:
        settings["resolution"][0] = args.width
    if hasattr(args, "height") and args.height is not None:
        settings["resolution"][1] = args.height

    # Default render dir
    if not args.render_dir:
        args.render_dir = os.path.dirname(args.image[0]) + os.path.sep


    stamp = Render_stamp(metadata, args.image, args.render_dir, settings)


if __name__ == "__main__":
    main()
