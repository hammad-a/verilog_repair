// file = 0; split type = patterns; threshold = 100000; total count = 0.
#include <stdio.h>
#include <stdlib.h>
#include <strings.h>
#include "rmapats.h"

void  hsG_0__0 (struct dummyq_struct * I1253, EBLK  * I1247, U  I675);
void  hsG_0__0 (struct dummyq_struct * I1253, EBLK  * I1247, U  I675)
{
    U  I1506;
    U  I1507;
    U  I1508;
    struct futq * I1509;
    struct dummyq_struct * pQ = I1253;
    I1506 = ((U )vcs_clocks) + I675;
    I1508 = I1506 & ((1 << fHashTableSize) - 1);
    I1247->I716 = (EBLK  *)(-1);
    I1247->I720 = I1506;
    if (I1506 < (U )vcs_clocks) {
        I1507 = ((U  *)&vcs_clocks)[1];
        sched_millenium(pQ, I1247, I1507 + 1, I1506);
    }
    else if ((peblkFutQ1Head != ((void *)0)) && (I675 == 1)) {
        I1247->I722 = (struct eblk *)peblkFutQ1Tail;
        peblkFutQ1Tail->I716 = I1247;
        peblkFutQ1Tail = I1247;
    }
    else if ((I1509 = pQ->I1153[I1508].I734)) {
        I1247->I722 = (struct eblk *)I1509->I733;
        I1509->I733->I716 = (RP )I1247;
        I1509->I733 = (RmaEblk  *)I1247;
    }
    else {
        sched_hsopt(pQ, I1247, I1506);
    }
}
#ifdef __cplusplus
extern "C" {
#endif
void SinitHsimPats(void);
#ifdef __cplusplus
}
#endif
