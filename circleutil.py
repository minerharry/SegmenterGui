# Python3 program for implementing
# Mid-Point Circle Drawing Algorithm
 


def discrete_circle_nonsense(r,xo,yo):
    out = [];
    xoffset = xo; xo=0; #no math needed for these, will always be integers; just adding at the end and setting to zero for algorithm
    yoffset = yo; yo=0;

    ri=int(r); # integer part of the radius */
    r=r-0.5; # circle of radius r'=r-0.5 is generated */
    a=r-ri; # corresponding fractional part of radius */
    # CIRCLE WITH SMALL RADIUS */
    # print(f"adjusted r: {r}")

    if (r <= 0.5 and r>0):
        out.extend([(1,0),(0,1),(-1,0),(0,-1)]);
    elif (r<=1):
        tmp=2*r+1;
        for x in range(-2,3): # the generation is brute force */
            for y in range(-2,3):
                tmp1=(x-xo)*(x-xo)+(y-yo)*(y-yo)-r*r;
                if ((tmp1>=0) and (tmp1<tmp)):
                    out.append((x,y));                  
    else:
        # GENERAL CASE */
        # Initialization of loop constants */
        rph=r+0.5;
        rpxo=r+xo; rmxo=r-xo; rpyo=r+yo; rmyo=r-yo;
        xoph=xo+0.5; xomh=xo-0.5; yoph=yo+0.5; yomh=yo-0.5;
        # STARTING POINT COMPUTATION */
        y=0;
        d=((ri-rpxo)*(ri+rmxo)+yo*yo)/2.0; # Initial value of d for (ri,0) */
        if (d<(a+xo)): # does (ri+1,0) belong to the circle ? */
            out.append((ri+1,0)); # (ri+1,0) does belong to the circle */
            if (d>=0):  out.append((ri,0)); x=ri; # (ri,0) belongs also to the circle */
            else: x=ri+1; d+=ri-xomh; # (ri,0) doesn't belong to the circle */
            

        elif ((d>=0) and (d<rph)): # does (ri,0) belong to the circle ? */
            out.append((ri,0));
            x=ri;
        else: # if neither (ri+1,0) nor (ri,0) belong to the circle then (ri-1,0) does */
            x=ri-1; out.append((x,0));
            d+=xoph-ri;

        # END OF STARTING POINT PHASE */
        # GENERATION OF QUADRANT 1 */
        while (x>0):
            if (d<(rpyo-y)): # Type (a) ? */
                d+=y-yomh;
                y+= 1;
                out.append((x,y));
            else:
                d+=xoph-x;
                x-= 1;
                if (d>=0): out.append((x,y)); # Type (b) ? */
                else:
                    d+=y-yomh; # Type (c)  !*/
                    y+= 1;
                out.append((x,y));
            
        # END OF GENERATION OF QUADRANT 1 */
        # LIMIT POINTS BETWEEN QUADRANT #1 AND QUADRANT #2 */
        if (d<(rpyo-y)): # Does (0,y+1) belong to the circle ? */
            d+=xoph; out.append((0,y+1)); x-=1; out.append((-1,y));
        # GENERATION OF QUADRANT 2 */
        while (y>0):
            if (d<(rmxo+x)):
                d+=xoph-x;
                x-=1;
                out.append((x,y));
            else:
                d+=yoph-y;
                y-=1;
                if (d>=0): out.append((x,y));
                else:
                    d+=xoph-x;
                    x-=1;
                    out.append((x,y));

        # END OF GENERATION OF QUADRANT #2 */
        # LIMIT POINTS BETWEEN QUADRANT #2 AND QUADRANT #3 */
        if (d<(rpxo+x)):
            d+=yoph; out.append((x-1,0)); y-=1; out.append((x,-1));
        # GENERATION OF QUADRANT #3 */
        while (x<0):
            if (d<(rmyo+y)):
                d+=yoph-y;
                y-=1;
                out.append((x,y));
            else:
                d+=x-xomh;
                x+=1;
                if (d>=0): out.append((x,y));
                else:
                    d+=yoph-y;
                    y-=1;
                    out.append((x,y));

        # END OF GENERATION OF QUADRANT #3 */
        # LIMIT POINTS BETWEEN QUADRANT #3 AND QUADRANT #4 */
        if (d<(rmyo+y)):
            d-=xomh; out.append((0,y-1)); x+=1; out.append((1,y));
        # GENERATION OF QUADRANT #4 */
        while (y<0):
            if (d<(rpxo-x)):
                d+=x-xomh;
                x+=1;
                out.append((x,y));
            else:
                d+=y-yomh;
                y+=1;
                if ((d>=0)and(y)): out.append((x,y));
                else:
                    d+=x-xomh;
                    x+=1;
                    if (y): out.append((x,y));

        # END OF GENERATION OF QUADRANT #4 */
        # END OF THE GENERAL CASE */
    # END OF THE ALGORITHM */

    return [(p[0]+xoffset,p[1]+yoffset) for p in out];




def midPointCircleDraw(x_centre, y_centre, r):
    x = r
    y = 0
     
    # Printing the initial point the
    # axes after translation
    print("(", x + x_centre, ", ",
               y + y_centre, ")",
               sep = "", end = "")
     
    # When radius is zero only a single
    # point be printed
    if (r > 0) :
     
        print("(", x + x_centre, ", ",
                  -y + y_centre, ")",
                  sep = "", end = "")
        print("(", y + x_centre, ", ",
                   x + y_centre, ")",
                   sep = "", end = "")
        print("(", -y + x_centre, ", ",
                    x + y_centre, ")", sep = "")
     
    # Initialising the value of P
    P = 1 - r
 
    out = [];
    signs = [1,-1];

    while x > y:
     
        y += 1
         
        # Mid-point inside or on the perimeter
        if P <= 0:
            P = P + 2 * y + 1
             
        # Mid-point outside the perimeter
        else:        
            x -= 1
            P = P + 2 * y - 2 * x + 1
         
        # All the perimeter points have
        # already been printed
        if (x < y):
            break
         
        # Printing the generated point its reflection
        # in the other octants after translation
        # print("(", x + x_centre, ", ", y + y_centre,
        #                     ")", sep = "", end = "")
        # print("(", -x + x_centre, ", ", y + y_centre,
        #                      ")", sep = "", end = "")
        # print("(", x + x_centre, ", ", -y + y_centre,
        #                      ")", sep = "", end = "")
        # print("(", -x + x_centre, ", ", -y + y_centre,
        #                                 ")", sep = "")
                                    
        print([(x + signs[int(i/2)]*x_centre,y+signs[i%2]*y_centre) for i in range(4)]);
        out = out + [(signs[int(i/2)]*x + x_centre,signs[i%2]*y+y_centre) for i in range(4)];
        
        # If the generated point on the line x = y then
        # the perimeter points have already been printed
        if x != y:
            out = out + [(signs[int(i/2)]*y + y_centre,signs[i%2]*x+x_centre) for i in range(4)];
            # print("(", y + x_centre, ", ", x + y_centre,
            #                     ")", sep = "", end = "")
            # print("(", -y + x_centre, ", ", x + y_centre,
            #                      ")", sep = "", end = "")
            # print("(", y + x_centre, ", ", -x + y_centre,
            #                      ")", sep = "", end = "")
            # print("(", -y + x_centre, ", ", -x + y_centre,
            #                                 ")", sep = "")
    return out;
def mirror_points_8(x, y, center=None):
    """ Return 8-way symmetry of points. """
    if center:
        return [( x + center[0],  y + center[1]),
                ( y + center[0],  x + center[1]),
                (-x + center[0],  y + center[1]),
                (-y + center[0],  x + center[1]),
                ( x + center[0], -y + center[1]),
                ( y + center[0], -x + center[1]),
                (-x + center[0], -y + center[1]),
                (-y + center[0], -x + center[1])]
    else:
        return [( x,  y),
            ( y,  x),
            (-x,  y),
            (-y,  x),
            ( x, -y),
            ( y, -x),
            (-x, -y),
            (-y, -x)]

def F(x, y, r):
    return (x * x) + (y * y) - (r * r)

def circle_bresenham_integer(r,x0=None,y0=None):
    """ Like draw_circle_bresenham_integer_ene_2order, but use 'f_m <= 0'
    instead of 'f_m < 0'.
    """
    center=(x0,y0) if x0 is not None and y0 is not None else None
    points = []
    x = 0
    y = -r
    F_M = 1 - r
    d_e = 3
    d_ne = -(r << 1) + 5
    points.extend(mirror_points_8(x, y,center))
    while x < -y:
        if F_M <= 0:
            F_M += d_e
        else:
            F_M += d_ne
            d_ne += 2
            y += 1
        d_e += 2
        d_ne += 2
        x += 1
        points.extend(mirror_points_8(x, y,center))
    return points

def circle_bresenham_float(r,center=(0,0)):
    """ Draw a circle using a floating point variable, F_M. Draw by moving E or SE."""
    points = []
    x = 0
    y = r
    # F_M is a float.
    F_M = 5 / 4 - r
    points.extend(mirror_points_8(x, y,center))
    while x < y:
        if F_M < 0:
            F_M += 2.0 * x + 3.0
        else:
            F_M += 2.0 * (x - y) + 5.0
            y -= 1
        x += 1
        points.extend(mirror_points_8(x, y,center))
    return points

def getFill(points):
    x_rot = [0,0,1,1];
    y_rot = [1,0,0,1]
    if len(set(points)) <= 1:
        return points;
    infill_points = [];

    #sort points into lists by x value
    y_points = dict();
    for point in points:
        y = point[1];
        if y not in y_points:
            y_points[y] = [point];
        else:
            y_points[y].append(point);

    #iterate from the leftmost to rightmost to get all the infill
    for y,row in y_points.items():
        leftmost = sorted(row,key = lambda p: p[0])[0];
        rightmost = sorted(row,key = lambda p: p[0], reverse=True)[0];
        infill_points.extend([(i,y) for i in range(int(leftmost[0]),int(rightmost[0]+1))]);

    return infill_points;

def getOutline(points,midpoint):
    x_rot = [0,0,1,1];
    y_rot = [1,0,0,1]
    if len(set(points)) <= 1:
        return [(midpoint[0] + x_rot[i],midpoint[1]+y_rot[i]) for i in range(4)];

    outline_path = [];

    #sort points into lists by x value
    y_points = dict();
    for point in points:
        y = point[1];
        if y not in y_points:
            y_points[y] = [point];
        else:
            y_points[y].append(point);

    #filter out horizontal edges; only select the left and rightmost points of each column
    x_points = dict();
    for y,row in y_points.items():
        leftmost = sorted(row,key = lambda p: p[0])[0];
        rightmost = sorted(row,key = lambda p: p[0], reverse=True)[0];
        for point in (leftmost,rightmost):
            x = point[0];
            if x not in x_points:
                x_points[x] = [point];
            else:
                x_points[x].append(point);
    # print(x_points)

    #for each column, find the corner points and add their edges to the path
    for y_sign in (0,1): #start with y so we always go counterclockwise
        x_keys = x_points.keys();
        for x in sorted(x_keys,reverse = bool(y_sign)):
            # print(f"x: {x}")
            column = x_points[x];
            x_sign = 0 if x <= midpoint[0] else 1;
            # print(f"x_sign: {x_sign}, y_sign: {y_sign}");
            point = sorted(column,key = lambda p: p[1],reverse = y_sign)[0];
            # print(f"Corner point: {point}");
            rot_start = abs(3*y_sign-x_sign) - (1 if x == midpoint[0] and y_sign else 0); #stupid math to make sure rotation starts in the right place; add one when bottom center since would be the wrong direction
            rot_len = 3 if x != midpoint[0] else 4; #if x midpoint go all the way around
            contour = [(point[0] + x_rot[(i+rot_start)%4],point[1]+y_rot[(i+rot_start)%4]) for i in range(rot_len)];#contour of corner point
            # print(f"contour: {contour}")
            unique_contour = [p for p in contour if p not in outline_path[-2:] + outline_path[:2]];
            # print(f"unique contour: {unique_contour}")
            outline_path = outline_path + unique_contour;

    return outline_path
                
def getCircleOutline(center,radius):
    return getOutline(discrete_circle_nonsense(radius,center[0],center[1]),center)

def getCircleFill(center,radius):
    return getFill(discrete_circle_nonsense(radius,center[0],center[1]));


# Driver Code
if __name__ == '__main__':
     
    # To draw a circle of radius 3
    # centred at (0, 0)
    radius = 5.5;
    center=(2,0);
    points = discrete_circle_nonsense(radius,center[0],center[1]); #NOTE: This algorithm doesn't quite line up with QT's - investigate
    path = getOutline(points,center) #this works perfectly for any given outline; just need to fix the outline


    print(points);
    # print("\n".join([str(i) for i in points]));
    # print(fill);
    # print(len(fill));
    print(path);
    print(len(path));

    

 
# Contributed by: SHUBHAMSINGH10
# Improved by: siddharthx_07