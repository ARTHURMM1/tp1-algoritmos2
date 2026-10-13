BASE32 = "0123456789bcdefghjkmnpqrstuvwxyz"
def bin_to_base32(binary) :
    return "".join(
        BASE32[int(binary[i:i+5], 2)]
        for i in range(0, len(binary), 5)
    )


def geohash(x, y, precision=8) :
    if (precision > 8) : 
        return ValueError
    
    s = ""
    #tenho que definir no mapa qual seria lat e log extremas
    latDown, latUp = -90, 90
    lonDown, lonUp = -180, 180

    
    for _ in range(20) :

        lonMid = (lonUp + lonDown) / 2
        latMid = (latUp + latDown) / 2
        
        if (x >= lonMid) :
            s = s + '1'
            lonDown = lonMid
        else :
            s = s + '0'
            lonUp = lonMid
        

        if (y >= latMid) :
            s = s + '1'
            latDown = latMid
        else :
            s = s + '0'
            latUp = latMid
        
    return bin_to_base32(s)[:precision]





