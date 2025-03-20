if __name__ == "__main__":
    from maskeditor import editMaskStack, imread
    import numpy as np
    ims = np.array([imread("reset.png")]*4)
    print(ims[0].shape)
    masks = editMaskStack(ims,None);
    from IPython import embed;
    embed()