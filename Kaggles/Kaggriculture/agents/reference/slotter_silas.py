# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2026 Rayk Kretzschmar
#
# The MIT grant covers the code in this file -- the market/SELL layer and the scheduler.
# It does NOT cover the base85 `_TRACE` field plan below, which is the shared public meta
# line reconstructed from public competition replays and is not the author's to license.
# See NOTICE, and the "Provenance" section of the dataset description.
"""Slotter Silas -- tier 8 of the Kaggriculture reference ladder.

Meta field plan with a reordered SELL layer.

STRATEGY
Same meta field plan, with the market queue reordered so that premium goods take the earliest slots of the turn and the glut-resistant staples fill in behind them.

WHAT THIS TIER TEACHES
Market orders resolve in list order, and the first unit of a sale gets the best price. Reordering the queue costs nothing and is worth real money.

FIELD PLAN -- READ THIS BEFORE REUSING
This agent does not use an original field plan. It executes the shared public
meta line: `scripts/cross_team_identity.py` over 530 downloaded replays finds
identical 712-turn farmer/hand sequences played by large groups of unrelated
teams -- one group of 29, another of 15, another of 8, with 104 distinct teams
appearing in at least one shared plan. No single team is credited because the
line demonstrably belongs to none of them.

What is the author's own, and what separates tiers 6-9 from each other, is the
market layer: which product takes the earliest slot in the order queue, when to
hold, and when to liquidate. Their head-to-head ordering differs from their
standalone bank ordering, which is the whole point.

Measured end-of-season bank: about 162,999 coins against the built-in
`starter` baseline over a 720-turn season.

This file is self-contained. Rename it to `main.py` and it is a valid
competition submission; or import it and call `agent(obs)` directly.

Part of the Kaggriculture Reference Agents dataset:
https://www.kaggle.com/datasets/raykkretzschmar/kaggriculture-reference-agents
"""

import base64
import copy
import json
import zlib

_TRACE = json.loads(
    zlib.decompress(
        base64.b85decode(
            "c-rk<O>Z1oa{Mnm_ksPvFW<OQ?~Je<QJ^R{)&pWNfY&f!tPf+~4F7j)#O~^<%E-vbe6LB$JGVxQ>U!Um880I8=l?nTw_ktz``>;$`=_7JKHYx)eD<_B`}be}^I!k#>la@?{{7eA{^M`|{q^(DXFq;;*na)j(T6{M`RgyYA3ywbdv~@tdw0J(TPzP>f8K82fBo{O?cM#yv&H4?>)nsr+sFOapSO2+$FG+5t2O$or~h4yTmGjnAMW1&^0obsU%s_%=)%uuyY1)4Z>{}!|M2+Z+0(RBzc=dB!~Od&?;dCEO7wF7-!A5@`t;%5U%q@A{jX88_N`frKRq{9XyD3g*SrCDx9_(5f1NyiK3<(#@%hK?_7iHyVIYqGbJUp6_h0spw#}M-BeZILoV-~p{`~uFO`bfRpw)C7wzvC*BM-<@SgFG!hp`$r=-sWEj^V5457P3TJ@fEmaQS^*BOf1!tvY@7^MNpaWc<t1HTQM&ZXdS~;qOLEY<ix!3;lUe@sJJ&!EwEzc1-7QXaHDe;qn?ihzv43m%yp$574~Hvxe<Q0ImD+ub_$A_duGd*;Dt!4cFW-6~l+ziiq~uezc$eebR>gB%v8`=ZLKT!<fNIKMv^VlX{jYZ#_H2c3@{8NMFdP&G)o2c(b3Yb=j^eJK)2V!ts9o#HP>;qCGM4uYwJVWAp((?h7-nLtDrI$AflU7Q;}@n*#?=@9s)?3xOk<ZI#r5o%O|jV^3#&scwXIiI$`3CqMNQVU#*avnW1%hw<<kye#<xcqDj?b?)!(w(lN)`SbSS@x$GRf0-<aR4l)4Z4-EF(RX*T!$HqmA2f<5=>uS#nd=h%{n-(!EvQW@l70Vh|4DzusD1W1U>_XM$>%KDo}p5PkT?{<gY?v_(jn;$F#F-diN-sSkAF-L(1UCjM!U7}=FhdfGQ^qo?Y9h0C~O1uSlzx@X21_@`tjl5N#PG3!<Ih3M;jQAt<u2bBcA{5b=#Mn`^pavV^HX@9Y6AG@Dy%{cfhZ$`bRr*R3(BICya$u6yxTEQBl)z-#2cO(uuwSRFCLToB3RpKYQXb!VgMGH4AIrfA}G>UNSFPlPk~P-py@CKe)}q#EDMv6uBup^YN*+Xo5y+!%M+LLdt8$hHS@SIc69D$gIAC7^rJg8rGBfnSAvWhI_LY=mL%-dQvs&8-CQLQW9wX_2hfFPd>^Gx0L&bT%0+N$x=T&42d7W)_(Yyeto|`Y*%XhvvP3PH;9`=XhAdwp@Kz-QoK0GwfqN;;)dDShuPNx6#XKh-n?O#PhD{|Dfmk-RVN%gz7Mo;5N@6868P0WO!TlF4VAy>0pWd*;UWk^P981#xLFb5qbLds7c-ar9za|~{iIOoBw?WK$vpb)46*h4T`lI*PN{yOpon_?5g~Sf|CT6DdsRfRDJJQH2JQoq3pe^*zQko|EyO*2XxZ;pw-P|IA?Xn}(rGvyeE8$-!#_u#8zDLSYC3+3bC@YczsAg7f$QgWZeS;sC@waD@tG}%TR1%Z_|?!jcPu_XKHTp9w0(H^t0iFSY(JDK9GW_Mf<p%cf9STiKm$a3z(%#XMao!K<6jyrgzaaKoD{AM9yU9_H}6xTbA)P09&5h=Bas_ZyWBbBl9E}&*qZ{^E-YKT)Q@4_Zck|I1iMV`(}@%|4Wd^u_+GUE)$Ui_(wAJ<T&8I@l0N*<(m_Grz~y=*eR&H+!#?_$(*@P*69v`wh5mvewG|PS5cS%~413vWCeu2#j?wWvoa@dIiq|jQvClnfn*vT<%!AVM4X_IkbQlFyQl8P)A)Yz-;;ByEIj%n-HS5%&VTt)DTq@@Tp)QD_v)w4DYsS)xiQKH2FKGvH$lQi`Y9s(k&^`@38bE$_Wx*bv=^zN+$@LZJpU4qe5%{c)7J6zP=F9(nmuT32GyBjJLk80H*9d&CT9H^N@s!ZUQweFBfXPhCPz@}DpccF^TO%g`&m{s~L7qx9xZ|(`$<AdRQvDqOy1z3`%CP2XzykoQFi3B>pCHEozpmFoIrd8T;pRRh1P1sb{5?z=3xTHASt8!mK~BK+^mq}a(PZ*bO1_z)VfdYPe}BhbX_;LF@(>pxvm+6JHsHyGivS}26ZsWTuE?xmsT_m()(8TkTGzqV_@&@Bz?X%E9DFK475W!6WYrOgPgeGDFJ{f1-C>;0AJEV@OK3?xStDTd6?m;%XbdL{()Vq;yZ!jSN5sycyb?b+6040be>a}bm7Ur1zWBQcdFvx^(M)J@9hq3Z(lbYhxg<$2zBz^PdC+i_D)Y8fgBFIM1>;iu_ljQ-^)CSV0i?aUe^v{g8Iy*somzgP+|Vy5yI@8hslNy{hboIx3SSke>0p$HS2KHjOqWr%5CKqydx_+z=&|WdEjDFH0!w1@gPJisLOXjau%b&tS>f=|v}0I|);lS+^p-VqGXOA1+=&)vE1_K|2~kk&rbDCr&~0oV)?jZ*@9My6W*~phS<~8u){glQIIgJ9jmwJuS8AYWY^FEVO#Af<v^_J~pn;1}xAlU_XFUsT@GX|pyj6!h71BzZw4|AF6qC*2^;NlwlJn1l*y6+8U%n;Aix)^qA-xyh^<@3*JPI3w4T=e_$ryQ<A<(Tv*SQ{w6Lg1#8wK$E;VVXCo52li)m<bw3dzY4*<J-$0{vmzN=$YZG|BM#7?F;U?9~f)i7rY4`N^%Wi(AadOKj1B3`uxLN0X%A5zp9ho~+@xJX!7pm+a9$n9E}Hgus)zfF#SVtC+qDfRc2h843XwG-#CXX$!OIoa|_sz$SusA0u#@oiJY@D=AY7##&;P+O-|NzK=8pdrEm5Gia(EX7B>g@FxuC9lx5BKRUEE4C|r>^TWfWs!_}7incqDM3{?+UV%}M+3I#LM3wf6U@jd(dR;qLN>+J3@FCFx)j+}u36%mh@D$yWgxSog2M5-cAZ;vTeAsVhhf;1fL97w&-OjvM^biVffT&)gvg)@Q5QgZ)cU@j}!Vc`3YP<jI2m?6bFsy}A&HBf87AJ-^Mhqm%9DrXMEDQXaLG0VE;FsNS9L{a_=(}nEhtu5W2h+ye6Ls>4huk{(+o{?OxV$Vw)(Ieu<p@CXH(rl8$Ua!q7F<LUtB*@~%K*+Yf~CMzId7q`TQ0s<6RIC43sJ)<b->sQ4=ojA_6mU=tnk2v#9sA>p=sXYYn{4@1`Z`OrAIva!}gdC`nRd*JkmVQw_(||MLH^}IgnIt^)$K%)yGkEgGn8~5y3Z3+0Ev;p>mdJYAA<aE#$J+3U<;6mL|IV^=$iy4hGHnS}pD<ol1%=WY}8%x+vN(Qihpr^>ES<m^6_6wv%NDHw+z01si{%o(HKd3(j`R^q~g}TCK_XXP^jLUK9&q3Aa{WO}odx$w1I_P&uoSNg3K4ixhE0fH!HTWumo?SByA-?udo1Hi}J^Kf-=qHSs;#z>(E=363mRZyg;Of5}qn(xjdDC$@x?oV27_=fE_=3Ymom0-LB~ke5UXy!Q9Pfgs87AtJEsIGN|<=*d=~JxJmYofwjzf~B&e?AS*F5q(O)?NJ6WB$0)fZ&2w-hV53cCug`4(NCkeQpl<Lxi{*zq<HVyy)jK_n-uM!y}*qW&pZ#V6Gxo}8-e%{><sLHivG(ymntTfG{6lvhYaJjX|M`#AWxXkC&r5@Udyr+m{S%2(=nN340T>I7Q|++y2XOwEiE5vmTZoz(vTa@7_%B2s&$*P;})gGPsn{W&B=43F2Vjm)0$2gfhIYeT;mv7dyt;T^SC-ErK5Cn2fm4EbFF4#++`n#vhxHr>Y73|ZTvv71;i}Xxq|DbBzGfv-7`Zr=HJN#bE24Oy4aQ*NBz7``Nx0@9%L&Zt+iSO>gf@-Y9_55&O&c|2*R*>MYv}Doxn92f8*DLX21`9ThFWZ-rl?rNK<63@NiK2bb0~{GHROX$kWDiVp;L=`{9zD1)ZoQA-Hqvt0@GBk#_iop*9dQQ2nes5MR1Xjlm#v+Z1a0Acz~<XNO<A2C@dCOqx$|W!&j)IEXBUuRt~Kt-v6O#B&9yJj2Vl8zFVRU>s#xh(Y<;OgI8=cFAoyvz~PL7=>EgXxjv+74;*xr%(o|WZ9%Wq8SgtStJ4wkN0i`DvDU|tU4#7Z~!eGD=5_qG_>%G$oS*56?*%4biq`qKx_k2m-~=enWkJo{am{e5hQjTzjG5=j;_=WKz77X%8fQl49;w7Hxt$*7D+gJX>Ad6ETKh7wHgc>x=33s(qNkCe5~cXc!kW>b-mPzG$~f=ibtyejB;`D+G=mB(|XYdkl~fsajbiC`iy>q%u?wWg)5S6E8;b;Oq|i1Y}c0%_0iluOPU&Qy|ESE-sz*gmY80$N;CI7r3Wg(ScY#D-jiIGH|6zn@l>q8Kp!kQjzlMoW4|zI|0>}cV|xbT_XvZrbJxNfitX1oHwgnS%IS&rOz3$NXTnq+cCBNY`+j6>62O?-{YElp$dXY*Pul_1Tn!STG7QEJa0NDORxU0pA_5RR+QF9WO!SIs;JT10GTi&w2vBy{J3B?qS#w-YK|<vav8-Ysaob=Qm2#8<|H1V|EGP)`i%_R|gkKqlfF<_$+07D!F$RPcd8opnmOSRXh1PB6mDDPi_gqXL<DAKyk^7a+-Axlv6cAlx@_0&W0ObRoGqL@5kM}>_KHl5v13U-KRitj1#AL6>g^cT+ai$LVF_&l4F4H6a%VzaCbo6Zc&r2l{HIPyB%SLnfJZ=OfzDU`nlC_5rF;Yl&iwmVQ8(l4PuC6ey1WQiE^yH^cJe68&NtDj#r?<c<pj4YbK&tNuq}sd*jH={yQ-G)(U*krON~oL$;jVURtd{}=H-7|#O5_uiZ6h&&>JUw0S%AS~W1Tx%nrn-$6F3gI>Ss6Pj35Dqhom0y3|VM~Ko|h#05OhT{nM9j<(ec5$e=dNyOqG2DJzTrPNjFUttbItC{2r9KU1(QEPn7Di*Mo{@rp}Zq0}jxle}Tk%HC@v+!sWr1q~HMj#7TMa2W9h_Z*&Cx*j=XU9m1VYz%ObF3F+-n{I}PQs>qBhNjX$@Q;a?x`Z9{DJLC5cLygl`{v+mlv7Q_P6BZOZ#3(vBGiReL-{&WiSG!Jxx@G*x*e0PR7TY?R<X0p;Ef`An$F+=Yz=F;eg3?@F!;vqu{kIf^+b03O*qf_wT{M6hku)UU5A6n<_ta&(;o6a8~5od13#j(kN|O1Fh|~u;auWKV$+v)#dNGKgschsf+ibotLAmP7N;i!?ea!BjbPaNv_Me;k*Gjp<}Fn8vV9Fom(AThdRMLrSO=aHhW8560`7LCOYCyh+ISjT=sG3R5iS^b{Q{7*O<U(zGI7;g-e=hryVYEJl&-2<bX8)0ftd)59*;_}ro}nwC@NIH0^hBj0+Q`zq>0YRE?-H>We=*8Sy`jVNav2RB!<3a*{j6Y@~*QeB|Tdhqz5kD?J2|k#zpi<(IWvg7<~eNMpZ_NG%{obO!nWmd-bbUyAl4$;$6D6mv_;UuKosz$ol0LM>Yg;A9<riOgha=jKXIz7@m`qk~2|6L$@x;SicUm=cN@eQXpseb5v#`rZ)4mcqVX+w-{rk0Fq=}Sz28)31Oz|cV)S&h&f0kX;$mS55=<YHQa7&>_JB~VVb{(N%H`p&+MV4k!0Fof|3_ox$~XA049U<Z!ywJmh9D2qOEphBzGlk{<Q;QzojlmuVrJDG9zpDvTC~V34*UB|66{S%qlRfCw9_irf>boR)qrH9qrFy<AVMcXjgR@$&_$u?_Qx)H`Al!=vFd}lodGQuClsPAQ2}Q*9wjlO%}aL->Kr#N-Ey=n_RWCsFSrQ{fdS1*j1P<#SrylIX1=o7(b3$5LFPJ2HH}z7=S60irtCyF0xl{^kt-!1lKDDh}VE%NLZ&lVX)l-;P9d835TzuInI=rNt)oq?|}$R=t4G8yw!=8Rr9NtFb)eXXB?AU+d1A^`F1Fgn3sy(0hcjwcEc}sTYuB}e3+c<H9QS0%jTHCF?L8GK-wcey2nid5)Qa{8E-?xO975yZp<Emr*=ZP`xFHnX~zH*C-5;=x$$N=BsZV}e>PJ~&7h&&GUt~A0jMrH9?meC9H0|3q2+p?0?#PdHjDm&4ImJ9B~D*rmh+X~ZSha@jZ4NcHS<ml*?5)K3P?a}O8MHlxf4J+yiC<eWpirUcxrTq4*~am(sS?^V+pmOIW*7HE*h)F%KL*iI)l&N11ct)q6{Kj88||xGz_t8+Ce(mhijKAa}r306{RN@P`iSyR}tx9YCBoY=G5$Ksv%LTO6$~TFBKPH7yNp@E|}o})Gg6qwQN^~ra*!kv243i_l#I46ixM)DfW$;6|e$Y0(#PizNY!qL?!!JyLGY%O(Lk$&@oGAOgi%p%ScBPLQ!5Mp1YZ)&YVQ~KPILOQft2~x>(0f01vEWgF&eWNJw+KDiA^xxFbOWW*`Ig@1aC44TaZjx)UcKt)VK~Ux_E>Y<#L%4y-q-`yaAfUB)L#=xas$brGBlP_nAwp#@`UJg&+)MUBi6gAtZ(o_=G9xX<5QI@r$j%Zk5Z6yTyCNv9^Rc*`&jU8il>O<aKW^`M)u-2J3PDE$S4Yg$l5NrzrU@g<pVhpQN=7IZ`99>u!2)XRQQ3ag!Tl0e|-t+vY4MQM6s9x$=<I-?^|OVs5QYN`gYA^=}H-QJXxS}6J>woHi&WQ{UHCr;9BF_s?HDhk(^CBG<RbHyW0N(!Js<8<Eua#*GLkj0OxRc+(s+-s`jo>8(G3si6zqLdL=8XhY?OTre=G@Rh8L^%U?AhN4vNdUzY7~wvjNVb^OzFB1h^8vkI@Py6PKrA4<(65#q1@iQ(n}i0}=64|V1j<c~-h~B{oc=Nyh_xqwNXQ8T1WvkT5g=NMw;h)a=Ppb8f;$tY2D`k=nGYE$PZBJM_{uJKQ)O2Ld&dI>pH>e~vWu&cjSd(K)82`;L3;UJ%GENGwIf(LG}0?oAa1~6B2-_01!QG!6~$301UOOePi4ow{zLus2S2D;>V?z4<?5ALLSeG3)QO|U5pP8V1~@eYkO^ac!aM;2vGbSb7(tvnK~7Lg2yLFa5|1>pmqz#qjdw0zKnw=u1MnstfKP&U?{IU{L>iLrz8#uS?yZ7s<yBj#iDP0Pxkpj9!s677;ws^(BN30FXB_h#bD&%|9fE!N`Xdkb&>s8Jq}oaq63x(u`x#MqLqbPu6)0D6k0pz6RXU0f8li>&K><8`etoV1TB|0Xadb3_*W2h{y@f3~UyTtS-_5qrZ;Let^NjyFP$AJol?VXwx|IuDYTPzWo1gR3b6T$5BgIg+R+r2>o*G-6aCfKY1i%?N^;8Xq-QsHIwQ!wb^zkAPc5Wt@>O#db4L)GiBekk5)Q4GuKbjy<0w8jJ5E;W(c{UwEusYr1a^dYoh{5qvvyufCGgA-z>4+K9cqd(gn~O5c6{8f-k60!EE&wYiY_iuty-4A1ne6h~Y^n<C)vJ8k^(%0vy89dDl_hy_yvY?kDO#XMr5-?SbX=s+J7#1=%rEUcBirHJg%!oBbcg3aB9Sn4=}>ZR;RI(1K#Lhe+Zkd?Mb~>+*hgYVSa2_R(jyOc9lOH6Briulj!sRkHSQq}we)bY7$J>s*mAGE_&w;MWbdvL_HlCU%x$ow;#-4@7I=hJCZir-66Ya*2eN7+FNGxw;S@!Rv~7&!Dzd06&i=`7S<lvin~Q6vT6}?f3LI%Xru#6=K+w*_;>BQcRgo;!s)urp>T&9fEi1_c0+$X>o5{C4FFI#e20j}py~A!s5`smjqIfY8L0rN4q2=O}MUtqdDPD<6N>07ly(R+ntp7xHFa<|xle2bj3C<BBP|~)GBPwZBhwJ_YyGD>};POT)h5X`FkW;_LtNtcawUmx3orVnkuP5hgvca#-bb0RJSFfQ)Bp2Z8?@^5CPQiDkQq(LT=f}m(|4WsksN&YC-7Wnyt+R-d@V9#1Wn927$23^pFmpT2vZjm5G2!C9m1?R<65bj6pd<DO&?|;ZVpO0|tdE9*(P%40`bxFxS_}3~<%|uaIzWJ-6e}Jw^K3Ds2a?SfXYgW<&dTf2{nMww9&5P$FvQh`OEsl8lwG!N;mXONLqhl~!cnD7v`#p&vojd{5kAU1glK*^<q#qwguF@6;sVWQ5Tiz?BeN|Ey9<jEnciL{aG99V9D(=@>V4kAIid?8+u-fw_=7oXEf+5r$}IRYQMoQ2wGdO&8Bblg$>^y(xRFgd6W=p@FHX?TYo$LqPdQnnVOHW$*s_Xpo-oF=B@^^kHzH@4kOQrQY-J|$6K*j{3scMcvS_CtMZ;+lm|LxoUIR4)qpDSYgnK3Y;hTW3)zZGxRxcrdjM`$}yQjuW6#76n`WP7S?}Je$aJ%0?mAnF>EQM=<K{EgCEkRx>JXgH1l*}4VXu&S>=2#fZ3h1S`@F}=*({~7nnW#l<3C2%)2umx3qat21fqLZBLvPX^5i2)_(}e2QdQp*!nx-XSy0Hq9yM%AtH`@$}ofww`WV&BF3zhl<qT@jyYw8e3qG&Tm&f(VJ?28`O<+6ukkZNdE`Dmr+XE`Q-m)6pLfj9)%*o+qGCgd)GAlVi49pI*=xCCJa8TT)x#;09QrQ?+R5R87nRXUje<eQAd*@5RZP5SVDkuE^Q#YL|(@C;CcdXH+j^$`gLh%V{MqDSoVu)k`Z9utFBDYviOXz~Bo=vA<M(%rro(<l~cd&pjTq!)3i1Ja4eR*w$$&X=GvRib~RI@RP|W}F2>3MEY*hDj*)<ZvspQmOqN!K>iddpS(&xg}R-A}?RWQU2wOzh-x~eksJO{wUT652l=!(-jM}3-MK;u3#Vpd`s}1S5U6(`1RINmad3(6EsG5h!2A`aEe*HNPR*E*b%v<Ua?TAPgnxOAoS(5i`nsK46c%*l8Y4ipMqrx#}BC>d~8EPjgULmJOg<HqpSeY8&aPpO`J9vNDV|y&T>R9Tiyy4T-PM<Aeg>u@*1vCr)*y}4RFMi(v-m$eTZPedGEm<;WXt@>^}IM;Q5tt)uK3yVhm~dy2QecD~d&GPCW90G<kzO&Jx;rE#YM>c$%?0Zbd#Jql#OzZ4Vcb2Sr3C{$1)v*!JT(*!HbKJ;xY*h9|#TvmwxyxY7V_N$u01L~oSB!_AI3{;>6{AxP@GsaVb9+by&^HYWQO?Z09g5TG&5^^18~9;?N%+p4$_CAt}aYcBT_9VVxNN~Ry&-GSBb?9+?oDzjiH;2)^0{enTZ-In1Svh~KCqt;ZMjMp`DPY5hvjG^Gm$t}lCy|SbBGA?GwVXY><l+z?N0X!ic4Max;Q#1QtTKfCia?C2@OJ@UVa8|0T=%!6d6jSS6<R3<-;qlg>2N-8@C?+|yu$xx?QgqmI?jTvk!BXYG@V`g(h^EkL?v`)O-WzaAHzj*1W|JmQAETD&rcx_lH*s0ET4#k@CCCTglZsf+{=I7L7uLG6RIeu}tWWBz6+jIX|H@6Pt&vSU*f*_K?dwb_dg{?k^CQY75y>s1^&*zxBVjt{KRPsAnHv|Vw#C}$;|VPn9t>4@91Gm0U@nDTqSRVUT|_`jY?_(xD4UXD5|kq%R$L5t3}^);D%emkgHg=v8wyNtSkhJ_iL@<g7*yD~Dn&GOgV1?CgcxS_R%vgKEPx2e>U4!$l#}D^xoz#~rYDKlO26G<;sd}p3|WS8<qdkv69uW|WgWu6c?-G7adD^Lc&}Qn<M`W#LT15KseRG%0j=fU+dZx<6488>5}h9OJrENbZiDEZ6r~UH%K%Z5s~H_h%?^;(z$gUOWfg!|Lgi0vpC)4D<YE(~SjNw;8SU#_2zB`#^C1u6&AIb7yjbyqVsA<A8~mTZ76Z@i`72<myeMkK0#qehCjd@$UxXA@u_)Va1w$Ds8Y=ce_ZbNjecqfmE^1izF~{+UQcgEQQWB!%DkK6{9&>Vu=$H%!OqSzYmVr&M*p#}TA}dOkB5$&AC8%`5_&JP=2!2XqEe}zb_oljh%1E;^rkRP$2sOOZUrwuvWJr@NqfgMWTxH(r*BNk}<!X}@7Lj9tHp-eLKjWl#S=XhSWa*}TlB+?$k=pT^B`#G^TjsVzX|!cWY_z?S7W|WV8&C*ER`p9DM#t3ZZSmrp;f`G<+%0Lj5HcA=H>#Ps%=uQDIbs!Z07s%&f1*r#PPsi6Dd_=Xi$aa5E<M66Ebh%Uvt_JRy(t1SWX=ajY143K*Nt;uYPO|HNA@y|)sAO%9Hh58xg60H{Ir-tK**qVSzTqYdcW_@VQ>*R=R0&^?8Gt33NsVXZN_;QT&Iuv_`(Pd2_$@SwC%JedX^d#b@=VN>g7yTqK>}dx~+_#9diG)m$_4Jy^q(Nju}#;bmwJ~loFr9dk#Q!0%l6A#dMnA^;3t^t;6FE@dxFspqwRnbr4$eu(~f9)fovz0B9FZM2@<1oe|R74=^_0aWC;`f*~HP)&fkc@rn0%1Yr|j!4#-0&Rf-$4^Gx@Zk&}Y_Y=VP<N$BlHPMtfj%dsmh|9txY<rZhRJ#hcUC1lg&z$PfjsTCG!1e|eM3rk9>31*8I$i~E;9^geDY$ByJ(g-l3?6!sR4JyXwNFI3BP%|tR)qt;{o#kKe$c-Bn02noah~EY6{b$pAwVjB2Wy9bwodu0Al_>$;u-sDQc@DVsV@j@MQLPI{aDpT%NkM3LyCu;B3%(vid2Dz!ukEGN;FR&L(1W{#9xtt76go(JC!4JiflRyuu*(|URff+KDl<0Fb^|m{NS}`CfFy*>J=A2?xKo$BpZ_QQ@bAa@^G)bxJ9WwQR(kT{^#G{sK;3SJW&}eI-qyzNv^3q*qvRf<UM_1fjHdE+vGao?)KyHg(=_5VHkxBwtbHMCi3+qU6Qns$}IpbRTSk$Q60?ae@Uo<=Y4tryTXfV=1)ZrPR?}z_+81LIM61@KJ|Q++i(2W4mY`2i1k=mIZw71kjmfuIrsets?Tu*PS^gT>^@45X|`a|1wm4C(=a0<fi<`d%&t80_sKYLKM{!25Tb)%M^KHb>*iA|h{E;&EsT<TwUl1Stlg?_KHs8BCx&FfUnBFk!F9uCAn^@5xzs|$tncwkBB1g>2#Fuy99m&eg#Mp}lBcohGII|=He+<kI^_yen<UPRB!@+mho{;>H<|k%IXimca(09HlF%}?bm*D`W98qq)m{sp`5mcg4I?itTB$UZz53ZnWB)p#VkR%-WaJuP?O;9`4zJYxk&1M#OLwIdcS|{huufKh^)QdJuUwkp&^v9;$^S>ijy4I1f!w}Vd~RHA{AGnImPdmK!XmMv39K>^R-GfJpKeUcJjE=g$3Z0x3CnHbt^*IG0V2`7om>KMzNBJ;^snTh4%tpi*H}^y9Yp)}g{by%v?cmIc|)Ieu?K=sBvRD)2nfqEF=0LG48)dPH1D?2l2SEfs>|y!u>{wwiRXfBRn-?W8y`F2p3CB4Fbdb#)?_b1)#Jw+iQ42IwfNTriWN~h43;-stGd5nrk|TkOhOFVJqte1Xi6px3tLpjVgw3aT+CMN65Det`H)>Fj#9o`yn{AKjgsY(CU>U^!$LA?0*l4Nkf$~^!RCarCRxQW>G(z`$$@i)-H6ekj`hyX_LXVW(KctF=+%db+q-|D3R<%`1#p@U4hSF$qjF~FmmSToo>WDnF8RSNv=b!fcDYHUhLy?&VlTq_wBmx-9L0uZ(dO3aV{iFo&Te_9t+cyrM>L+9uNv=jEuBhfs#_w$pC{YeKOi(64j~Ymcy#QS#Cg($a>eSX!Eqysi9EL|KV%vweHe|zi;JC|{LWLv7i#tynR09BWXuJ9Izq116(W(T?xP!eW+qq1ly#-22)ex}B%D<QbsFsC?fOk(I(WDfzLbSa8I1u~b}-mQmEsfhB`S9kERa_>tg4E>`GcTGgQ3l7mZ_|lF<6S@XNI8r=YfPJPh!yPjOiOy4Jnqvl;%*o-bYir)f|Qxt1G;rr9hoGze#r??`M+udh!%!hIpdZPovrLlF19vHGI8k!i#B(B@%;Lhhk>NkT|CWZm3p)lS2-b5P;WHh-9;j%M$zMq!d~Xd7qsuTfzJhI$}DzHhVa)mcnJY?SPzIpv|l*E_PI!U2sQ?>g0&r3g*OT#&VS|3Z>lFa2v%8b11~mwceWYnxW13Qi6~9-X{B({F7P$2UO6YiaRz>?BLhgZE;RUb_lm6d=1pcCP0ne6MCh-^m}Pq5^L|Pe&Lu3On1e(vw&{!P|Y^bI$ONCavabgTBoS&1izD<d4xv%iqd+#e%PvFr(Dh%GZqV_8ZG=W(Rx><k@bs9e&4rK4L*eYEn6Bq;lUAri_x604Y857w<;CHt(I#FCG>eKtB@1`u2@c?8^Q43$t-<xqqp1U<0P37ldvChtj@X8R(H6H(QLt#z80Np4yXK`5O_yO#tIoqm_k5dc>{Zy$>gC#a?kQysg9!XS8@Rwpzj@SA^Y@6H9G;ln!C)hUTuQtZ=V5Pss%nYdz7x-WsV);2HB4lY%X0*z{+>{3YcyWUrDV6K{vqrW^TFj>*(hP1w8{zofYL$Z|{{_UaonQw-`a;E#PsyIZqa{o~0*Va&rm)wlvPt$mPbF(K!y|8MgJ)-R-;Wu;Mm*4)?dOMv8&sGr^w=-AMd5)lR_)*GLaXdd|alhNf#;3<p8z==fooo^t;VRGIo*AA%|JW1D-$`jQ?4`?S=QkIS1WZywO?TpL$%2cr+Md@E}FG)8**KV_dwQv"
        )
    ).decode("utf-8")
)

_SELLABLE = (
    "STRAWBERRY",
    "MELON",
    "MILK",
    "WOOL",
    "EGG",
    "TOMATO",
    "CARROT",
    "WHEAT",
    "FERTILIZER",
)

_FRONT_RUN_HORIZON = 1
_FRONT_RUN_ITEMS = ("MELON", "STRAWBERRY", "MILK", "WOOL")
_BASE_PRICE = {"MELON": 250, "STRAWBERRY": 120, "MILK": 160, "WOOL": 200}
_GLUT_WEIGHT = {"MELON": 3.5, "STRAWBERRY": 2.0, "MILK": 2.0, "WOOL": 3.2}
_LAST_STEP = -1
_CLONE_CONFIDENCE = 0


def _public_signature(farm):
    """Compact public fingerprint for detecting a mirrored build."""
    counts = {
        item: 0
        for item in (
            "COW",
            "SHEEP",
            "GOOSE",
            "WHEAT",
            "CARROT",
            "TOMATO",
            "STRAWBERRY",
            "MELON",
            "PASTURE",
            "COOP",
            "WEED",
        )
    }
    for row in farm.get("tiles", []) or []:
        for tile in row or []:
            if not isinstance(tile, dict):
                continue
            for key in ("animal", "crop", "kind"):
                value = tile.get(key)
                if value in counts:
                    counts[value] += 1
                    break
    positions = [farm.get("farmer", [0, 0]), *(farm.get("hands", []) or [])]
    return (
        len(farm.get("hands", []) or []),
        tuple(sorted(farm.get("unlocked_quadrants", []) or [])),
        tuple(sorted(tuple(position) for position in positions)),
        tuple(counts[item] for item in sorted(counts)),
    )


def _signature_distance(left, right):
    distance = abs(left[0] - right[0])
    distance += 3 * abs(len(left[1]) - len(right[1]))
    distance += sum(abs(a - b) for a, b in zip(left[3], right[3]))
    if left[2] != right[2]:
        distance += 2
    return distance


def _update_clone_profile(obs, step):
    global _CLONE_CONFIDENCE
    if step not in (4, 24) and not (step >= 48 and step % 24 == 0):
        return
    farms = obs.get("farms", []) or []
    if len(farms) < 2:
        return
    player = int(obs.get("player", 0) or 0)
    distance = _signature_distance(
        _public_signature(farms[player]),
        _public_signature(farms[1 - player]),
    )
    if distance <= 1:
        _CLONE_CONFIDENCE = min(8, _CLONE_CONFIDENCE + 1)
    elif distance <= 4:
        _CLONE_CONFIDENCE = max(0, _CLONE_CONFIDENCE - 1)
    else:
        _CLONE_CONFIDENCE = max(0, _CLONE_CONFIDENCE - 3)


def _front_run(action, obs, step):
    """Sell one premium line immediately before a clone's expected glut."""
    if _CLONE_CONFIDENCE < 2 or _FRONT_RUN_HORIZON <= 0:
        return
    orders = list(action.get("market", []) or [])
    if len(orders) >= 10:
        return
    already = {}
    for order in orders:
        if isinstance(order, list) and len(order) >= 3 and order[0] == "SELL":
            already[order[1]] = already.get(order[1], 0) + max(0, int(order[2] or 0))
    planned = {}
    end = min(len(_TRACE), step + _FRONT_RUN_HORIZON + 1)
    for future_step in range(step + 1, end):
        distance = future_step - step
        for order in _TRACE[future_step].get("market", []) or []:
            if not (
                isinstance(order, list)
                and len(order) >= 3
                and order[0] == "SELL"
                and order[1] in _FRONT_RUN_ITEMS
            ):
                continue
            item = order[1]
            quantity = max(0, int(order[2] or 0))
            if item not in planned:
                planned[item] = [distance, quantity]
            else:
                planned[item][1] += quantity
    shed = (obs.get("private") or {}).get("shed") or {}
    prices = (obs.get("market") or {}).get("prices") or {}
    choices = []
    for item, (distance, quantity) in planned.items():
        available = max(0, int(shed.get(item, 0) or 0) - already.get(item, 0))
        quantity = min(available, quantity)
        if quantity <= 0:
            continue
        price = float(prices.get(item, _BASE_PRICE[item]) or 0)
        priority = (
            price * quantity * _GLUT_WEIGHT[item]
            + (_FRONT_RUN_HORIZON + 1 - distance) * _BASE_PRICE[item]
        )
        choices.append((priority, item, quantity))
    if choices:
        _, item, quantity = max(choices)
        orders.append(["SELL", item, quantity])
        action["market"] = orders[:10]


def _terminal_liquidation(action, obs, step):
    """Replay-derived safety net: leave no sellable shed inventory at season end."""
    if step < 680:
        return
    shed = (obs.get("private") or {}).get("shed") or {}
    market = action.setdefault("market", [])
    already = {
        order[1]
        for order in market
        if isinstance(order, list) and len(order) >= 2 and order[0] == "SELL"
    }
    for item in _SELLABLE:
        qty = int(shed.get(item, 0) or 0)
        if qty > 0 and item not in already and len(market) < 10:
            market.append(["SELL", item, qty])


def _shed_access(size):
    half = size // 2
    return [(half - 1, half - 1), (half, half - 1), (half - 1, half), (half, half)]


def _move_toward(pos, target, tiles):
    x, y = pos
    tx, ty = target
    choices = []
    if tx < x:
        choices.append(("WEST", (x - 1, y)))
    if tx > x:
        choices.append(("EAST", (x + 1, y)))
    if ty < y:
        choices.append(("NORTH", (x, y - 1)))
    if ty > y:
        choices.append(("SOUTH", (x, y + 1)))
    size = len(tiles)
    for op, (nx, ny) in choices:
        if 0 <= nx < size and 0 <= ny < size and tiles[ny][nx] != "LOCKED":
            return [op]
    return ["PASS"]


def _terminal_action(obs):
    """Observation-driven final-eight-turn harvest/drop/sell controller."""
    player = int(obs.get("player", 0) or 0)
    farm = (obs.get("farms") or [])[player]
    private = obs.get("private") or {}
    tiles = farm.get("tiles") or []
    size = len(tiles)
    positions = [farm.get("farmer", [0, 0]), *(farm.get("hands") or [])]
    inventories = list(private.get("inventories") or [])
    inventories.extend({} for _ in range(len(positions) - len(inventories)))
    sheds = set(_shed_access(size))

    available = {
        (x, y)
        for y, row in enumerate(tiles)
        for x, tile in enumerate(row)
        if isinstance(tile, dict) and int(tile.get("yield_units", 0) or 0) > 0
    }
    actions = []
    pending = {}
    for pos_raw, inventory in zip(positions, inventories):
        pos = tuple(pos_raw)
        inventory = inventory or {}
        load = sum(max(0, int(v or 0)) for v in inventory.values())
        x, y = pos
        tile = tiles[y][x] if 0 <= y < size and 0 <= x < size else None
        if load > 0 and pos in sheds:
            action = ["DROP"]
            for item, count in inventory.items():
                if item in _SELLABLE:
                    pending[item] = pending.get(item, 0) + max(0, int(count or 0))
        elif isinstance(tile, dict) and int(tile.get("yield_units", 0) or 0) > 0:
            action = ["HARVEST"]
            available.discard(pos)
        elif load > 0:
            target = min(sheds, key=lambda q: abs(q[0] - x) + abs(q[1] - y))
            action = _move_toward(pos, target, tiles)
        elif available:
            target = min(available, key=lambda q: (abs(q[0] - x) + abs(q[1] - y), q[1], q[0]))
            available.discard(target)
            action = _move_toward(pos, target, tiles)
        elif isinstance(tile, dict) and tile.get("fertilizer_available", False):
            action = ["COLLECT_FERTILIZER"]
        else:
            action = ["PASS"]
        actions.append(action)

    shed = dict(private.get("shed") or {})
    for item, count in pending.items():
        shed[item] = int(shed.get(item, 0) or 0) + count
    prices = (obs.get("market") or {}).get("prices") or {}
    sells = [
        (
            int(shed.get(item, 0) or 0) * int(prices.get(item, 1) or 1),
            item,
            int(shed.get(item, 0) or 0),
        )
        for item in _SELLABLE
    ]
    sells = [row for row in sells if row[2] > 0]
    sells.sort(reverse=True)
    market = [["SELL", item, qty] for _, item, qty in sells[:10]]
    if int(obs.get("hour", 0) or 0) <= 1:
        already = int(farm.get("hires_today", 0) or 0)
        for _ in range(min(10 - len(market), max(0, 8 - already))):
            market.append(["HIRE"])
    return {"farmer": actions[0], "hands": actions[1:], "market": market[:10]}


def _base_agent(obs, config=None):
    global _LAST_STEP, _CLONE_CONFIDENCE
    step = min(int(obs.get("step", 0) or 0), len(_TRACE) - 1)
    if step == 0 or step <= _LAST_STEP:
        _CLONE_CONFIDENCE = 0
    _LAST_STEP = step
    _update_clone_profile(obs, step)
    if step >= 717:
        return _terminal_action(obs)
    action = copy.deepcopy(_TRACE[step])
    _front_run(action, obs, step)
    _terminal_liquidation(action, obs, step)
    return action


# ===========================================================================
# Market-controller overlay
# ===========================================================================
import math as _math

# Per-step remaining sell volume of this field plan, measured over c27 self-play.
_SUPPLY = json.loads(
    zlib.decompress(
        base64.b85decode(
            "c%1Fr%Wm5+5Cza*39{~j!?(Ii3pWj#)PQRsXp4SH(SNTlZOK$D%hrRG91k$}ECK|GWl5pP5&z!5eqB9m??2xC_S${8>%g|40o8~KRn)i|T_c-Ng)B~CGN496wl}hgs1QXm@KJ@zO8JSLEoMTcp!~L+F{jWC^e|LF)=(2sf$PIb3(SlNzsDBEF#JfoWe(t$Yj9w9c;Cbw<7UNFSXW_+8eK!jXnZ0v6}ZhU25LvUVmLTB{V)npQt&Tu2T?{8u6>1DeP;Bfh-txjrG(rgadmg#C&QQ5mb7*zObT%PjIEHq#)0xwmcrH0IS6;r%ds_7fjeO<R-XVDHtFe5b{U9c@TIh4Qa~f2^712`IfKEUA#@B*lD={N5Gf8RziqLrKOgSyKR;|X>+lpP>YsCQadB~Rad9Oo3_rH(mxt||haX&ATwGjSTv-akk00C3!|SKjX7dw65Q*tshG7_nVVGkyprl}RZvx~bgg>YpF-fdKOSG4qgU%8bqxwVs6t+gzh!`qtez1P$MN(W?6824OUyMG5Y$A?9(^>?+g>mRks6oAK>ZeGxbZYtsodn6F-$d?$<E};~EL)F^?O7_S=&9^w^}PO$2eRE-I>Ru`&4T`{s6B{cFwQ{YZl6U*zQ14uWyS3#%h2Z*@^*MPQP3v8n8;y4cWAPRbdmZHJgFv)oG)UwHJsJsBlnMRadB~RadBm-FjM*T{4I2j>|PvW80OtT4e<Ic^F9%mLxt<aObni{eUSnSOm>`25B5IDhw)1T#~HJ2gbkb)it^`?XCZfm;OhyiIuT((rx*gdOtM5Af}2MpCW=~4u!#b8dq^Fe(W!z<VQjEXR6G?ub;2p#H~XpMB5DU|K3=`9*UzC3<m5IO40GEoV6^e>(Kih?vsxDB>cI}F?O-s7>4zgO*m=mOMPEO7fFHFt)1`zxoKzFEYZV<Sf2W`*g3~vl6)Si2btbe1*(mA?61N3mCrB|}<jgtQPJ>6GFRRV=>G|o`Y7^F*FlVr6C;{`%5t~lbSY!)lcb=RE!hfF_mzI-r-D(o354i67ZQuEZwrOsCA(S1oU{8hVL>-fNRvtUO?m%zt9OxwICh{0%a-kZ?nHV;0J{oL}oHQfG!C2wLe($Yu`<RKME{uGWj?HT?+Td1C5YbH5F*r?^*4GKtKIO3v+vWF6XxHyrn;6*2-<p>3c(Rs!pD~m+;RUgj8S*-S*aeT2QB@B!|NaA0p<>w"
        )
    ).decode("utf-8")
)

_I0 = 10000
_PRICE_FLOOR = 1
_MP = {
    "WHEAT": (25, 400, "sqrt", 0.80, "log", 0.20),
    "CARROT": (35, 450, "log", 0.20, "sqrt", 0.70),
    "TOMATO": (60, 200, "linear", 0.40, "sqrt", 0.60),
    "STRAWBERRY": (120, 100, "sqrt", 0.70, "linear", 1.60),
    "MELON": (250, 300, "log", 0.20, "sq", 3.60),
    "EGG": (50, 332, "linear", 0.40, "log", 0.20),
    "MILK": (160, 122, "sqrt", 0.60, "linear", 1.60),
    "WOOL": (200, 105, "log", 0.20, "sq", 3.20),
    "FERTILIZER": (100, 200, "linear", 0.40, "linear", 0.40),
}
_SHOP_DEMAND = {
    "BAKERY": ("EGG", "WHEAT"),
    "PIZZA_SHOP": ("MILK", "TOMATO", "WHEAT"),
    "BRUNCH_SPOT": ("EGG", "WHEAT", "STRAWBERRY"),
    "YARN_STORE": ("WOOL",),
    "ICE_CREAM_SHOP": ("STRAWBERRY", "MILK", "WHEAT"),
    "PET_CAFE": ("CARROT",),
    "SMOOTHIE_SHOP": ("STRAWBERRY", "MILK"),
    "FARMERS_MARKET": ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY"),
}
_CENTER_ITEMS = tuple(k for k in _MP if k != "FERTILIZER")

# Products the controller owns, mapped to a reservation price expressed as a
# fraction of base price. Everything else keeps the tape's schedule untouched.
_RESERVE = {}
# Sort SELL orders by gross value so the most valuable sale takes the earliest
# slot; market slots resolve index by index across both players.
_SORT_SELLS = True
# Ranking key for slot placement: "gross", "unit" or "impact".
_SORT_KEY = "impact"
# True places promoted sells ahead of buys/hires; False keeps the tape's layout.
_SELLS_FIRST = True
# Only these products may be promoted into early slots. Empty means all.
_PROMOTE = ("MILK", "WOOL", "STRAWBERRY", "MELON", "EGG", "TOMATO", "CARROT", "FERTILIZER")
# Extra slot priority for a product whose remaining supply outruns the town's
# remaining appetite. Such a product is a race, not a hold: its price will only
# fall, so the units sold before the opponent's are the only ones worth much.
# Ranking purely by current price gets this backwards — a already-crashed product
# looks unimportant precisely when beating the opponent to the floor matters most.
_RACE_WEIGHT = 0.0
# Products that may be promoted only from this step onward. Selling wheat early
# lowers the price an opponent pays for feed, which can rescue a cash-starved
# rival; deferring wheat promotion keeps that pressure on during the early game
# when starvation actually bites.
_PROMOTE_AFTER = {}
# Products promoted only while the opponent's public money is at least this much.
# A rival near insolvency is the one most helped by our extra supply, so we hold
# that pressure on until they are clearly solvent.
_PROMOTE_IF_OPP_MONEY = {"WHEAT": 200.0}
# Force selling once the shed reaches this load, protecting end-of-day drops.
_SHED_PRESSURE = 80
# Reservation decays linearly to zero across this window, spreading liquidation.
_RAMP_START = 576
_RAMP_END = 716

_SUPPLY_DRIVER = {
    "MILK": ("animal", "COW"),
    "WOOL": ("animal", "SHEEP"),
    "EGG": ("animal", "GOOSE"),
    "FERTILIZER": ("animal", None),
    "STRAWBERRY": ("crop", "STRAWBERRY"),
    "MELON": ("crop", "MELON"),
    "WHEAT": ("crop", "WHEAT"),
    "CARROT": ("crop", "CARROT"),
    "TOMATO": ("crop", "TOMATO"),
}


def _mshape(func, x):
    if func == "linear":
        return x
    if func == "sq":
        return x * x
    if func == "sqrt":
        return _math.sqrt(x)
    if func == "log10":
        return _math.log10(1.0 + x)
    return _math.log(1.0 + x)


def _mprice(item, inventory):
    """Exact port of the engine's market_price."""
    base, throughput, below_f, below_t, above_f, above_t = _MP[item]
    if inventory < _I0:
        amp = below_t * base / _mshape(below_f, throughput)
        value = base + amp * _mshape(below_f, _I0 - inventory)
    else:
        amp = above_t * base / _mshape(above_f, throughput)
        value = base - amp * _mshape(above_f, inventory - _I0)
    return max(_PRICE_FLOOR, int(round(value)))


def _remaining_drain(item, step, shops):
    """Units of `item` the town consumes between `step` and the season end.

    Shops fire on steps divisible by 4, the town center on steps divisible by 12
    with multipliers that step up on days 10 and 20. Still-locked shops are
    credited from the day they are expected to unlock (one new shop every three
    days), so late-game demand is not understated.
    """
    if item == "FERTILIZER":
        return 0.0  # neither the shops nor the town center consume fertilizer
    unlocked = set(shops or ())
    live = 0
    pending = []
    for name, products in _SHOP_DEMAND.items():
        if item not in products:
            continue
        weight = 2 if len(products) == 1 else 1
        if name in unlocked:
            live += weight
        else:
            pending.append(weight)
    n_locked = len(_SHOP_DEMAND) - len(unlocked)
    pending_total = sum(pending)
    is_center = item in _CENTER_ITEMS
    total = 0.0
    for s in range(step, 720):
        day = s // 24
        if s % 4 == 0:
            total += live
            if pending_total and n_locked > 0:
                expected = min(n_locked, max(0, day // 3 + 1 - len(unlocked)))
                total += pending_total * (expected / n_locked)
        if is_center and s % 12 == 0:
            total += 4 if day >= 20 else (2 if day >= 10 else 1)
    return total


def _count_driver(farm, kind, name):
    total = 0
    for row in farm.get("tiles") or []:
        for tile in row or []:
            if not isinstance(tile, dict):
                continue
            if kind == "animal":
                animal = tile.get("animal")
                if animal and (name is None or animal == name):
                    total += 1
            elif tile.get("kind") == "PLANT" and tile.get("crop") == name:
                total += 1
    return total


def _opponent_scale(obs, item):
    """Opponent's expected remaining supply of `item`, relative to ours."""
    driver = _SUPPLY_DRIVER.get(item)
    if driver is None:
        return 1.0
    farms = obs.get("farms") or []
    if len(farms) < 2:
        return 1.0
    me = int(obs.get("player", 0) or 0)
    kind, name = driver
    mine = _count_driver(farms[me], kind, name)
    theirs = _count_driver(farms[1 - me], kind, name)
    if mine <= 0:
        return 1.0 if theirs > 0 else 0.0
    return max(0.0, min(2.0, theirs / float(mine)))


def _reserve_price(item, step, obs, shops):
    """Reservation price for one unit of `item`.

    A fixed fraction of base price, decayed linearly to zero over the
    liquidation ramp, and scaled down when the town's remaining appetite cannot
    absorb the supply still to come: a structurally oversupplied product is a
    race to sell, not something to hold.
    """
    base = _MP[item][0]
    frac = _RESERVE[item]
    if step >= _RAMP_START:
        span = float(max(1, _RAMP_END - _RAMP_START))
        frac *= max(0.0, (_RAMP_END - step) / span)
    drain = _remaining_drain(item, step, shops)
    supply = float(_SUPPLY.get(item, [0] * 721)[min(step, 720)])
    ahead = supply * (1.0 + _opponent_scale(obs, item))
    if ahead > 0.0:
        frac *= min(1.0, drain / ahead)
    return base * frac


def _plan_sells(obs, step, slots, short_of_cash):
    """Choose SELL orders for the controlled products."""
    if slots <= 0:
        return []
    shed = (obs.get("private") or {}).get("shed") or {}
    inventory = (obs.get("market") or {}).get("inventory") or {}
    shops = (obs.get("town") or {}).get("unlocked_shops") or []
    load = sum(max(0, int(v or 0)) for v in shed.values())
    forced = load >= _SHED_PRESSURE or short_of_cash > 0

    candidates = []
    for item in _RESERVE:
        held = int(shed.get(item, 0) or 0)
        if held <= 0:
            continue
        inv = int(inventory.get(item, _I0) or _I0)
        if forced:
            units = held
        else:
            reserve = _reserve_price(item, step, obs, shops)
            units = 0
            while units < held and _mprice(item, inv + units) >= reserve:
                units += 1
        if units > 0:
            candidates.append((_mprice(item, inv) * units, item, units))
    candidates.sort(reverse=True)
    return [["SELL", item, units] for _, item, units in candidates[:slots]]


def _cash_needed(orders, obs):
    """Coins this turn's buy orders require."""
    seeds = {"WHEAT": 10, "CARROT": 20, "TOMATO": 50, "STRAWBERRY": 100, "MELON": 80}
    animals = {"GOOSE": 300, "COW": 400, "SHEEP": 500}
    prices = (obs.get("market") or {}).get("prices") or {}
    total = 0
    for order in orders:
        if not isinstance(order, list) or not order:
            continue
        op = order[0]
        if op == "BUY_SEED" and len(order) >= 3:
            total += seeds.get(order[1], 0) * int(order[2] or 0)
        elif op == "BUY_ANIMAL" and len(order) >= 3:
            total += animals.get(order[1], 0) * int(order[2] or 0)
        elif op == "BUY_PRODUCT" and len(order) >= 3:
            total += int(prices.get(order[1], 50) or 50) * int(order[2] or 0)
        elif op == "BUY_LAND":
            total += 4000
    return total


def _race_factor(item, step, obs):
    """1.0 when the town can absorb everything still coming, higher when not."""
    if _RACE_WEIGHT <= 0.0:
        return 1.0
    shops = (obs.get("town") or {}).get("unlocked_shops") or []
    drain = _remaining_drain(item, step, shops)
    supply = float(_SUPPLY.get(item, [0] * 721)[min(step, 720)])
    ahead = supply * (1.0 + _opponent_scale(obs, item))
    if ahead <= 0.0:
        return 1.0
    glut = max(0.0, 1.0 - drain / ahead)
    return 1.0 + _RACE_WEIGHT * glut


def _sell_priority(order, obs, step=0):
    """Rank a SELL order for slot placement; higher goes into an earlier slot.

    Market slots resolve index by index across both players, so an order in an
    earlier slot is priced before the opponent's matching order in a later slot.
    ``gross`` ranks by revenue at stake. ``impact`` ranks by how much revenue is
    actually lost by going second, which is the quantity times this order's own
    price impact — that promotes steep premium curves (wool, melon, milk) over
    large but nearly flat staple sales (wheat, egg).
    """
    if not (isinstance(order, list) and len(order) >= 3 and order[0] == "SELL"):
        return -1.0
    item = order[1]
    try:
        qty = int(order[2] or 0)
    except (TypeError, ValueError):
        return -1.0
    if qty <= 0 or item not in _MP:
        return -1.0
    inventory = (obs.get("market") or {}).get("inventory") or {}
    inv = int(inventory.get(item, _I0) or _I0)
    unit = _mprice(item, inv)
    held = int(((obs.get("private") or {}).get("shed") or {}).get(item, 0) or 0)
    qty = min(qty, held) if held > 0 else qty
    race = _race_factor(item, step, obs)
    if _SORT_KEY == "unit":
        return float(unit) * race
    if _SORT_KEY == "impact":
        return float(qty) * float(unit - _mprice(item, inv + qty)) * race
    return float(unit) * float(qty) * race


def agent(obs, config=None):
    """c27 with its SELL layer partially replaced by the market controller."""
    action = _base_agent(obs, config)
    try:
        step = int(obs.get("step", 0) or 0)
        if step >= 717:
            return action  # proven terminal controller; leave untouched
        orders = list(action.get("market") or [])
        keep = [
            order
            for order in orders
            if not (
                isinstance(order, list)
                and len(order) >= 2
                and order[0] == "SELL"
                and order[1] in _RESERVE
            )
        ]
        player = int(obs.get("player", 0) or 0)
        money = float(((obs.get("farms") or [{}])[player]).get("money", 0) or 0)
        short = max(0.0, _cash_needed(keep, obs) - money)
        sells = _plan_sells(obs, step, 10 - len(keep), short)
        if not _SORT_SELLS:
            action["market"] = (sells + keep)[:10]
            return action

        def is_sell(o):
            return isinstance(o, list) and o and o[0] == "SELL"

        opp_money = None
        if _PROMOTE_IF_OPP_MONEY:
            farms = obs.get("farms") or []
            if len(farms) > 1:
                opp_money = float(farms[1 - player].get("money", 0) or 0)

        def promotable(o):
            if not is_sell(o):
                return False
            item = o[1]
            if item in _PROMOTE_IF_OPP_MONEY:
                if opp_money is None:
                    return False
                return opp_money >= _PROMOTE_IF_OPP_MONEY[item]
            if item in _PROMOTE_AFTER:
                return step >= _PROMOTE_AFTER[item]
            return not _PROMOTE or item in _PROMOTE

        # Only promotable sells compete for the earliest slots. WHEAT and
        # FERTILIZER are the only products an opponent can BUY_PRODUCT, so
        # promoting those ahead of their buys would lower the price they pay for
        # feed; those sells are deliberately left in their tape position, where
        # the opponent's buys have already drained inventory and lifted the price.
        merged = [o for o in sells if promotable(o)] + [o for o in keep if promotable(o)]
        merged.sort(key=lambda o: -_sell_priority(o, obs, step))
        rest = [o for o in sells if not promotable(o)] + [o for o in keep if not promotable(o)]
        if _SELLS_FIRST:
            action["market"] = (merged + rest)[:10]
        else:
            # Keep the tape's slot layout: sorted sells refill the slots that
            # already held promotable sells; every other order stays put.
            out = []
            queue = list(merged)
            for order in keep:
                out.append(queue.pop(0) if (promotable(order) and queue) else order)
            out.extend(queue)
            action["market"] = out[:10]
        return action
    except Exception:
        return action
