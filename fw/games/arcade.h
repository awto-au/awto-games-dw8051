// Shared by the arcade apps (docs/arcade-image.md). Include after UserCommonInclude.h and AwtoApps.h.
#ifndef ARCADE_H
#define ARCADE_H

#define ARC_KEY_QUIT                            AWTO_K_MENU         // front key MENU ends the app; the other keys are ignored (the demos take no input); POWER is the framework's
#define ARC_MS_HALF                             0x8000              // WORD ms difference below this = the time has passed
#define ARC_MS_PER_S                            1000UL

// saver_canvas.c: 1-bit tile upload + one char command per cell
extern void AwtoScTile(WORD usAddr, BYTE __xdata *pucB);
extern void ArcOsdMap1(BYTE ucCols, BYTE ucRows, BYTE ucAttr);

// arcade_snd.c: game tracks over AwtoAppSoundTone (cmd ids of the old player: pacman_sound.py CMDS)
extern void ArcSnd(BYTE ucCmd);
extern void ArcSndBg(BYTE ucState);
extern void ArcSndPoll(void);
extern void ArcSndStop(void);
extern void ArcSndInit(void);

// shared key hook: MENU quits
extern void ArcKey(BYTE ucKey, BYTE ucEv);
#endif
