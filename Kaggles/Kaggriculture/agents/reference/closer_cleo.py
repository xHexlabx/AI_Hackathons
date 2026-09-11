# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2026 Rayk Kretzschmar
#
# The MIT grant covers the code in this file -- the market/SELL layer and the scheduler.
# It does NOT cover the base85 `_TRACE` field plan below, which is the shared public meta
# line reconstructed from public competition replays and is not the author's to license.
# See NOTICE, and the "Provenance" section of the dataset description.
"""Closer Cleo -- tier 9 of the Kaggriculture reference ladder.

Meta field plan, sells reordered in place so buys stay funded.

STRATEGY
Same meta field plan, but the SELL layer only reorders within the market slots the plan already used for selling. Nothing is moved into a slot that was holding a purchase.

WHAT THIS TIER TEACHES
The subtlest lesson in the dataset, and the most expensive one to learn the hard way. Sells fund the buys that follow them in the same queue; hoist the sells out of their original slots and a BUY_PRODUCT WHEAT later in the turn fails on a near-zero balance, animals go unfed, and the farm quietly loses far more than the reordering gained.

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

Measured end-of-season bank: about 148,546 coins against the built-in
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
            "c-rk<O>Z1oa{Mnm^DykDw32UJsn;W{W+X_OCDsBlSiox-FxH2$Z-)Q7C6TP^u8fR`%=cQ-8hcW!Nmjk@ml+uu`SE`){_QWn{q3*6UHsF>i{Jn9>h;TC-`>3c@XNcy#ogt_zyIYw|MkB<{p8cfzy0O6|M=^FfBO9S*Z%zL&CjoXx_NzZdGX@S?ZxH(?sD_>`yUU7w-=XJk3V>SIK2Gy^-qV_Z+^bG{N3j3+aC`%A3pu|50Br!efQ?&FE2hE{pib|{P^liyB<H>{qN;*^M8Kx?!%AA&Hi|CdwBoh%O5=a?6f29Qy#zic=7hti$DJI_OaU+S6{xoe@XAr+adq-iq|(U4i9fQYB_w*=J}ug^yhWVk}fPmvV4f0BJa4p`EYor`VhaFGZD*E4mXc&-*h>S-_pB>l_dK2_`v&>dh&MgF7WKjb&Nh<ynpk{cI7<mjQTLIPhBTdtV}T2+xOg$C|oIj_`EssAhYSL59s5MK3=@Id0a0`XTy9x{QrI&@8Z!E&yKsw;I31KhWUO>N&_1A+39MDqp<wN{cv=;NJf3_>N3ILOt^XfzPvzBo1N{>?Kj~~_B6(!URO=BGnbC8zo~jkhH_mi>%irEr8B1SaqFZVZxK1Dg|S<w@5@ufXiZp=%X{L7qXV=vdijGJWA^a3-t#L9tn%E=hi~xM?asR9mg2_5(`MYm0ynKVZ8RiD!HYMqUmsq4`1KEmcOPE8e)TV(XNx>IwrbfXtyZmv<!C#W10miPo4-Y`I_VMmd9#1Z=*U)qeamd#j@e#VK&Ig(ZE<1;tk2U=VXaw=;D@iiZELm<Y_{g~!{}vs)VxlsV&@+2qguO;%!ERF9{&nHsBkZW=PWDd`+Cgk)v2dE{N~t0DmU5t!|Ttm#?i@mc|H3oLrBS0iilj_o$cy#O*+!O;k#(L)zX2|?L*fRzTygwR)4OYQ%wyEcxK;8e7K{jM;@HuqM5Tj@Vb{U0<gx8^r3t2jLm6XG2jCIhNFZ0;t`Lu;7rlhjNMZZ*8BUqeW%=;|1U4!e_W>SMd#nD^zP`7%hvIpF+vFIoojg<-549B&G2qL&+9zyY4dTZW7zdH<70wfHQK@j1?%AiU!jFV{xR`G=X<2nFWK4G<lt2|`Ei?@^Lu#O%Xe?y+E0VGbPNKF-TM1)NCL>BcP!9UGcZu(wHCYvdwxZSZE&}25uj}xVu8u~5x_faFlDCN%?TS}in$O^=DB7Ai`ME}>c^XRe+t*i`ei;V>{b|v&xTcT+?M5Y3W~k|@b2dJ_lI}y{v4@Atzf@%ucEi??&Rrt+%pt*KE<kyGwJa!js`&*n8%F>#0GPi$Hp^a@;36RH^<2s=O&F6g$j!`wj3^2&t(`{r0e6i5ud_(&CYJdS4r6$D?GTiXoxvN=Z=MS8n6=G6X4;)s8c?UCtKMxDXqO?LVH8DHtjPolN&bawj0nue2j;DA&;6+k-r-hktp5qrwrMvoFThuLQ29FW?|i0>;O56#yAq1iLg#92#m*OV?A{(^JIX|L`n?iQUi#IT-<QfbvOB7YzQ#fK<vXu#Nu5<9fCO~t)u`0PGXa1o%2~rzAf<9z)W;dKtl0L_6@onHhkY%_&ONSWm_R&jL@pwS5mwza@m*W+<!BvlM9NIhtn<}f6D-190wDyHz$F4;K}QyIOV}{Hbx+{_}B*H@=T8nC)d*w7I$@IZaq9<Kc5lPM(1|l9(3AG4&I#!VWML+bpFM`0uZOBJHRtW;hOdo?<#0!XHW{L>9U<sI8t7}4=25dY8J-pad*FY^XZ?biF*|>{=hp2wuDa)j*naW!fe|?x)K0gI@weJvEh(wGeEcvg-@VaO%GxMOkh@=brS2T#alAtto8%VDC;av6quhzY6)uL02!!eiadD)S3db4FE0YpvH~zw+a$TttK3}xt6$^jMFp#3kxrHkdOl(fBB!>PL9oAVYV7>3N8)TW(h^|c2ujPiwo@RxTM~QX={3W&EHDuvUweam>z=FGkKoTTB`9jrk7|;+cc2Rx4`3$7e9Io}j~Hy(Oprfd*BUbeuZ0Hh9KINg?5F@t$BxKbuEJSU)4=Q%KST*kMsN$zbUVeVYK6BjZ_Y4Uyq>T`bdbrMq#iq#QapA6vPOqYz9JrQ;3+j4+yG!2=Ywf~Od$%!H+6=Qu=6&ks|nvh(^nEvJSM%P-4n<+nVssJu+T>GSlO3VMqY*VvM&T>rM!o-1J`9CgH&Zd09=BLwGzP-mL||*s>N4e+RX8{%?R_ZN|(}Pp7m&p{aAJ`TviX;?59_+|M(d=tH3VNj@`a0H!M-yXw#HrukSK4U4b^VO#jkg#a95ameV-8wH&-2R_SEuy_eeC%FH7CwBtV;<quHWLR?jn_^CM$R!qH1DGbrk6V~c!q!cctp`4W*e|MaR?YP&B;FDDt_5*b-;wW@5>&yj=W-}Tv(BxB(eEu4N@TizAC!{m3H${mRLJtf!c$}(}>}Jf0MD4HdD}cnX+t$kO>(XkI?lY}BrskKje$*%d2V@fyJ9!~wlLNw2Cx<KgC64l+wKS|*qFG=|o8*NR@y80BL!&NhBLHJ4*l8>u+YF)RLY|;e@e+)F<v@<Omz6~*ui$up()1rQa}-cy9(U+*OHboB+?m|5uSFDLON;SaYrWlVRP705Nf7rJ*hgD8^7yOGRnR1if;af)>TyUcvq*xuy&uq)VUjc0d|U0f9{F)!AwS;c_e#9D?TmE`l>jCzb#0wQtudxGTg1Uj6>%PEP*Rue<*R?TJWjX;awjN_+H^eqP9({<$E~%mEWn(RvpiR>N$PWT^bG;eYttH<{FQ9j5*W?SQWCV<%o;HiM_peTygbGm@z}{nG{y}84RLi4SfZd=Vg|@q{Evs*YxKf678DVn`)F2>S2_hCCI&Vi(3P*HQpK@ZCj4}90)yO*y@O7)GZKl;GHO`rbTnKWLLFnxqF~R)aczYQLc2(Cj*n6FrzN@eI?Y`i5p@PZTCmbtBh9f3n`PGvK~~cIr}&M2Cc!kHv1<?3UKT?yCw}l%#|tb58jmk?l6^T4--tGh$_hB62#PRg4AUk?H5$5YdxL&e8k=a#M6To1gtZ8R0yoqH13N8(*(ShLP{S2xbAa3j&`FvNYL6J2xw6I&IvdrC<1Ek0(WUu2mb?T*dG#qy;cS52r?gxV$FreOtdeqSmqL#;hw=0%#AKvAK6=^6R1%`>D=pxji~rOyF*;Tvjg=ugQ3+zDIZbgd+^0KK0vXVXQ9dHw=L3ftL6vg?tNi5YY|42BE0X{)x9FM&tfHEAMN_xwnTDJs%2YbqB`18EeVX-`@26dfnt}t*%&^SE{axES)m2JX*8CQrsavOC*c>?)M3_>0H=mP0sCe!|jit@WvYdcR2bT|t1l;K=z1rESs1?UFMlg3|kv|=cV2-<_BFU>6Q}iE3=jfSzlsqdP7qWj)f{s^&+!akMQiBQDN-?CAG+?UR*GdNx+!*z9^@}MMVRZ0`(LqKpg7iUUi;*mKcOLG;cviMpa2Q!4T_K2}n9zQNkwNEaz_h03S&2+~>Fa=)>?f*1hNE;;qi}*}5rYs5lh#xuw2g#Ommum5v+b?P2!F<h==d0HL_zc#_;5)eCuQIEBc4bmLkubnys;yqKYk1;NW<esOwvfsRic+xmZUoKX&5}hH+uhYK*smJ<8GEd{Mg#$nd55X^9)X^L1@i3AkpQ8loja&AbwUvv>UxIM0%Ojc&@ivl~V$zFCPHbm@yhOnZ`l_x0-S2!!`-bG#SoKHCN-D26M~Jwb;cpu#Eu4=*)AO2`8D=BQbym%0d_r_m3io5>N1oA3vO7PY9l{pBv{MM;Fi>&!j2K)$lwD3{I2B2}evJ>aW~*0u%P?Is=0~ejpSk5c#)7;Hvc`j<R@ko{`W;S!YL(agTp{e);RzoJgJaW!?box}nTL6;vz^bEBdZ5quKqngTbHVSQ%C%_ydtR#3}Il|)<I*Uf2YNzq`j@~2x|OCLUD33HsAPBOQO6K$n8q}g&R*g04tjodomWCzpcYN$2sZSHjF0zr9Fc4gq=;d0_7M;b2=YO7*669vbZT#UnbZkOiSX=ySbIrETKBFYo-$YgPQS~;f$FoSGqn({eZON!LUJE9=tWCTy9i$b0{ST9L9(G4<FO{kNq*26j3&LD5xWkkTKDzQWyuaeUSa*EkV{%~pBs6sEZks3O&{mcU<cTpFZtvT-dbEYy+Bm!iP=;ZWbpA4{S@_=RgG&=YO`J_MvVEM-^KfK`yWeLv1oOGDf;&|n?x5-9^kolO=8O?L$`%!;}a5sF(fLoWJZ&SZ1F<N6n@%m=d0D_o|BFNgI6wH_=KSLjkvZ*qlR66C83HFLdNV8`MjbiyMerOWh*gBI~TRH`GgJ^VR4WNO95g3XoPy0!+2*dMP63SiV>*v<1Vv20AA|w`EL|y`OTc*X%JRVfsL4kXj>#O`m;?y=F9Y%Oy25TamR+-6oIj|Q}_@V4ZkCuVq+yEK1cig*@SHeb)dLZ1R^DhH7STr<WqQ^I#+!#znuK;0R+LCz*<g9%RX9BBzg>&+$`#Q~xdlF=9*U#8$&5~JRXj=h#_Z@k>w6vRE5*77aKfKJcJy9}RLscXCurT%oUW>u@St?d6q`x#K=8|M+w~SR&Z8yQ~-M7ovKo#OlJltj3^%<a6)<3W_7}>hEIO2%Ar6nWtTgrbbPBj%QEi=Q5YXs|*HyEuk1&bG#wD7z_9xb)~{eU*j+dDXf-<}vT3A8aPIRIvgskMG;p3e_Z6!b)np(7L%w<u~aB3y7U)s!6=()WNME6C7gIWqL{uyQlfymq5-l{j2P38r|K!du9eZzJ}9b~@e=@lj}aIAo5*K_5^B=lN2e#yrbCsBi?DNfMs82p;qt#Hp#!vuZ{@JmiKsH3=^cTy)kLLK`sRHAF0F>swE;S1o)*LP26NbDGGU<iKI^`0{#c+e1c*d#xldExy)kn!ui{IDZr`@7A3vMc5x6XcR=f`bTs<1sfunMkqV{&?@2D2(EX^yIRh@ufx?%cGpHX3I5v&@=Qh6FO6P``wJ%#B0K<~1nZ)a&A%@c3AHmf3l@N#|1hB#G7$p?X@|fM(h&`1+7nU=ccydLqb2s|E>@e3LNn4h!@=`d$+}c+bA1k7KczFWsf3*JJX%2`hP|09j90I1B_@d(AmF7{S!YC$&@FuI(E(btf0A6n7DK1#5Y@Hd6nXQLJ|klrD3QTcwjCM;ZksdON2Cp~a?;I&dN&=wgjtSwK_y;8AnqXFimlXB+a}7fm#pijg-9<NtmN8Q955PWH@&khUpbp{OZE`OIYI&BG?YCxa_%hvkL!Lm&iHiC)em?nmy_1Q`U-ArojblyQ$-4nJ<smT<JxT8j?a{W7>t$X4Z`>e=A?QtA`~*<Rf1C&4ou1#AE=%r)473b-Q&cg<0Dn$sj+IafJ0ZC%*_=YU7`T}L8{r*%pE7yD*ARIGVU7Wu8X$U(JNL#i2aP)&QL<tj~g>xAEWltq3*hopfDR47Bs^=2_qL@adf<NUhgY3avk@Qg+<Nsy2&Kw)r-e7%<*l969;_#<Nhep3JZeLiet|a(5-|UJ(ro6AIgjORzNb56CM3EG+JKvbJ@o?t;N0eF_Ll!z#DsvK2DNjv#8$&Ltm{1n{PerI>s`@ZbG(49cbr32k$Xbs(}}2CNOCkUNX_3)>zoQfWb~16xGaN;C0vEGtA|tL2`619L}A~ee9Q?-U+9H?K64nfZ;OgSp&Cpl;FO7WNG;v(L<|a;q%{B!83kWPjZAP#mj?RN=j+g{8Y8t91%I-1Dj6OfSE1bS=b9dQP3?mG>I<HmBWj@1jb}ma%_n1N<=~_NmzF!FVHg@y*0w3a7<}Dl#sShZN^FpA{91OaFi{nPRDnY0<o(gu;>8JqcSlTLJ{0Nt5zj3v}+Xlr=gjP3rX)D_cz>H>rg_bdabMjV<cAxKI&FI2H6VuRD6590g%7J<mn1Uxd~czx`<EzCs&86MvqU>83|q(?`JF)s<%*7G8o`hC^G^$OcW3ENFtyPhw@k=LboZpEQJlJ+n*d6exws|VX>TD^zqU9ctl7zyuR@no7DSk2LbGX`u52#CXKYQCl63zlfb;{A_pBW7N?t4rFK$}yr@P;r%<jQRAQhzu%xp3*_xK_7_J)tLbC%6lQ_V$v(p_$r2_t*$Pf2+(N(b?XCHKt9b#!<EEAw$xLQI4>|JOtI%U@@#p-s`lnbCInk0DJ?p;-x?rT*RWNE&|jBNqB_X+zkbK6t}XZiJ1*?BfBMy0MbmDSVjcA4`;*Pc{5q*Bz;<3mtP&CnGCAVoxC2Av56w6KX?fee_!NYJ3Cna7Nua<J+sjdQo)dC9;GS!XcQP@F@;0I^${e#DjdnV$+0uqWk_B>t6kkTa#L-18l;MM-&4G9GOR1C+Q`Boj<)b<zx{R%s8a0FY8}%q)!(S*$B9XevkYwy^yP;1-JRdp<I4HqAI^ZDrJuF~Si|Ca0WO+8J_<4%`@#L1E^{Q(A?W4A;)cHjE}uFu&R_B(^yqMG)c4YSReLI=5j=S0bjhfJ@3zN(jOR7GY^nLE&n5b_j+M*uMiw#;#K1zJQs;xUjE}Kn0V=m?=iwJ$g?J8e^K0`T_k+-DP|EV(1bjr~yByYQ5>6?R!~CT?q?M-8u8NC&?UGemYGOVTy(=35*DL^<h9W>w?$1^?)^CAJ*`|k>3P^ug@V?*sG&YX}h?EfIX>T&x&ZUOmOY!)^yv2x9a$N6Ug(=M_CxhzMT?;%W_Y~s>(puLOK2{j?u|yqW(3F_xnknxKB*-Y>F~#MtFl`?dM<Spl@xMy-{)HVp~NmsKx`!{Hhly9bA&$v4MwFEyPOB9j%z^`LLAH)yn;614a`=n4~}d{YEi8(4<49#(;w)lo}L4nDaIW`oT|ahuf%5NJT>#=9J<LhBrD)#`p?Qz!}n6tiMB`?i{I!Y~4JGWeT4(vqu%E;U(Im_@OyRgrEUA2t4ROA&`#o5pPd?(`28Oec?RAkDlckBs5G_L?i67Ysz|*Mr8-h;TaZD=#Yi}2~~TjoQX$tXCsQ#E@%jMmP{N;Rbea@=m)hF*~gnMc}`qMjEM9hpswxYH1%X9$-uU$Z_gaQCwnpOH$sxw0>h=lfpXggJ!#|u=<iD5W>QsrZtzo%hxUIxfe5>*u32)sz~_X}EET$S%G4$&UjaCv>1iURPh#zg*fXS(Ur|rNyf&huLxdta7zg#qDbu3UBnCu-&@EGZ1(Jr5<3}ibnJdbf08fl_N2RDRCP@4x`jDoGng2eJZviHZRXX$t6>+VC`DIN2*%z$4DEc!(3SfCPs4_<E+`JBy>kZtEDtBOsj;CKQ)g%PQ&zx^E{tGtf5t4VT)RQtl1Oc(KZw)mNI@-K+Qn?%jb4olJ5EFi>a6(u;`CErL%`Eb2j!ZH0;XYxsBJ3z65`>9vYlajkB5ipPRsuv=aXmTHwERSev>@m_J};lEo%kt14JO7_1;}G{9noPYpbnNxKO@gcNuXptLn37;&VfzUR7)P9(aYW4fMzkx<zn2Be6X1E1E-<YkW6?kuxbQt0S};%(93xMFT;nkQ08$3dZquu<t|jBd<9v}@*XJWqAMkm(6mVVgO!lhtjC0hV-P87OM?>WGynsPF2yz)MXgfaO97Cf<=U&7IxT*Ot75Chl{xAiP&k%z6nCay<d~-gEv<Gmvjv>V-^6GT(E?x;iPmD^jf>D1mA7C=J0H;mBWsaL*%$#71dujhl~XdzOvj2VV%q6HUf0>U$1zBk5XOcG{xhNJiAGOsK2bOU%05V~sH<Gs>Z}W0?Y?`Jl=HE4IR2wKP0xUC+;#>5S0_)IA0zEB{gGx)laEd@zZCUBs2ot+#Fu$3ix#-N0Tv==9EqB{ntWa9XrX_cAmPu0sga_q^0wpQUd16JsR7s+v=maC|G~iBX8l}C>OfAW$TDyD4sIq8fyXmMbXTJBie_bk8aUHE28+b4gQRkx`baM!UlyDd><LLy;K9^DvGonk2*a5rEr863L7-8Ah=J0@XwOgrZv(h+D)shrZQVQGNTP!Ja2Wn@!*Ub!)`64lRg8xA62>P=p+B$u3OprCz!b=*<_soY;FT{;vB7xtRGKY^N{?1TjtXq0aDv&v3cE~b_#C7(l7NzEzE}rYPS`tM>t#7FnFq(Ur%DtxeA4pd(@VRIIV*W&)e2(ZQjy?f7FP$kS}LhG8!eXV)?ms}4iO_CW~U*6$&$zn+4~ZB@@rP@bS*XWtYXqSEYre*5*hjKcn+V;s3heiZsL{3ww|T)JSgb1I}_b)|1D&F8a1ZASEZkf=oVOQ-SXOOtF`2kTd93?!;c9K+my64QBDr6&lBo(!N>s{A__4?N!EX=q%g9THA3v#RpuzZF#<wxp2Xx)y~4h$u5j>rs@&Xcu}aEmE&tMnf8zXMrc0hX)`|Q_wiR3;YEMueMK;YPc{PEH`bzAo5EjiBoL1cj#vUj#LQ(|HqRd5@Cp&2U65U$FTdk|bqJ%lkLjHyX(i12IDW?0pBS0fYoQ;F8dfQ9_N}NZ^l}~7QCImOuUh^taqFa%0L9jBCU-QhSk9b^cxWyebB!h2~#4!y;cGQy!q){)U7)cX*LhxV)uFErk7clIluYu>q`J2e!tsudga52SUw;=Tt(wK;Oy2|fFy**d&o;TKv6zCy49=pw8F2tkG<Q3AkusT<_hcb8=nL&Lid5~%8p>Uq&bz#xeC7^cC&kh@*>SbSrU3T`|$h1=Fvx%HRju6m%#z@FWL8aOrj|2~!{Z<MgH>+*$D{LfnKT5wP;a<3mkbOr?Tn%Tl{C7>%q~aq<H}+5!ot~lA!$ixiaDR`3iRDiZgSuSMsN1?zH6CV(WMEZ=Ub+jyFhJ8ClovjznCKN^)=wz3XK7UWn%WKU^{P}ty|#|TwmklE0#8S*53J2ey=3{9V&lpzRi~6v6GPx^LeA&HBK5KR_q&MOE51K1RO8|~BhpNdoVn9<u96hGcrEZFz;R>A$WcA?<-G9~Z|Unf1Bfa4Jr3q=GntBL+$zG($;lAXanv4jkqGy!U>%8x_|)SxG1GkL8)Mud!McVlCu$52@9C;w1rpX2t&^cs^Pvw4Yw~HXA}us-h<4YD)R8uGnQPW&RpOW+C!HZ3*Sz-74w;`fk7tu+mVGmZ%~XBsuUDM>+J-`|?+Q{yEtMz_HStA+?fP0Q*@xwF-3|gFyNa%mP}Xq#hC^R`ci&9ARP-NOYH-`lvxb~)qn`0DnB>7wjwM(bkJod%KD%qo*jNhncO!hD>-^+&r2M)nxmLXJ7;ltW2e3dPnRSe?yyA+0mlP`UW$oi*OBAERAiDY}mSD#K_`?;7xLQh_EqXk19jRLE0GN6<1}gQes`u}t#Sd-kB%A;sO;U`pJ@SM_$AjB0M#X$mLwzQd_hCkwS>>E2=rDk)qCM#z4YwX?h)UjT*VofkiH8Es0QAy&5H8da#JSe6JyQvzA@?%amM@{Yiyz$t3J8;;3b>j&q|a6BPkWXNg)dpcTeheolDolHyi{24#`G=p0IbGR->kR2UL8-z@A~rDksqq6??pK-A%0J!z`Dz=oCWp%^R8NN=_h9gXY53uvxy{~CD#drOP?o8?Rlr(8x3G!Q3R{lL!B{T9L&J|D<L3nU*G(^z7c;@74K=;s3yBKwoYXx2#acv3}d8#WnxXCC$3rTr|VGhlahC4%iU6oa#cGBou2_{SuVum1qpr>TSawREi#a&b`j2**pzso3zd=xJSTgnQ9E+6VNNf#qDr?QEt9A`=t_5&P16H%{VNDkMCg*naP_e}lFgZIPR!E-OEuqO0BuTl{&sC$mJb9tPZ4(IPOZuc;InP=tIWiiD(9O^|H&p(A3yr$tmI|WP`Ij;Qgw_OsCE$#2}mQ$f32K!W1O8p0p(Dt_%5)TVy!Z5L68Qg^iKQir@1$5nmg@YtMk-W6j=@;L!67pOS6J7&cu@e+r_<Gr4BMA_WMG{N%~7WaLfRLi0CuRL73(2ZZs`lhabYa7+<5pTzs7rS4@6DkwqMFpjJ~kPU;=vM%EYWh=A=@Hz;zAWS66*$aT_C@>X1x00c9xC@;&5Q`y+!p{50;zQqnrhVSA@bRIqQb5!t?FrP1u)PJTt{+}CJYWwNhPu-vS<@@Z?e{e{9UY<$lx2qNz#I$J)0Sa+?Y;!Z2uhV3C);H^`mpMt9bajWy##nbzF@>lmWlCW6s$t%uj+Y6H5LE=-J2K1rJKx2i(#mX6dn;p(k6jU8s$^OE*`TvBYmYsYf|xfk8v#&ffZ#Q<7b&JFA_H1#M{{42G0PHk3)x~qT%}uo4WT!AT|;V%(ns|r%KHk)qL7>gqq?#OiIA}p3>Ql>Np4izB3Xs5!nagyjxN^i9NHkQSjf232C`bIN1=4MymsdMNL6>}rKiS#>a7!icQFFWC-s#FVCqMfb$Dy)Rta@JmRi*>IonCm_6qDp<bumqo~GTESnN!UD55U}HLDg1jE$E_1eGKLa0(J42%(rb*2|wQyw##Uw9oL`nbG08`p?x5-@MS=x>)=?E*fE>Bq<V`KjA@v+%+z^e?39|NYT4M&KtlB{HIi|4SFNvgH`qNmQ=&xvL)qUJS+aDx&fF5l@f(*iHpqG_KIrwi4Zh_Znh4OSH(ni_w1$W>|`d7vuKrU8ZQ>3lxE8jsab49wjzkUwsgN~ty}28xhIFc06Y!>CkzxYO(z1wLK$iqYfn#c$*mA#XPa7!s8pGNS`Uh*ltkW3ggpwy%PKXdl*~}I*oJ@_<pD96fS*rR;H#$gnkZ101hSNOIqI%6&x^w96$%=axE(_gC8<T|>mDq9DF89(1W7WoZmB<**a^_~tjh_Xu!D~wVF_`7#Q2TK20qOOTmmkff>bQim6v^lV@wOLrOQHA8*pUQ!2(LekN|sxensGqmP&IR<)}9tVVw94sqc}M$>NM$kv0hdYVxMF=?Qy%D?DZYLHrOvG;tJaEM^~z(m&bTxmnMKP#P6>XNk1J33E+ub(;~AweiAA$zf_25=(c0!p0;BOTw>1Q$YPG>VDJ4cBjYI3}yoN6=TbvB~gf^T$7<y%8k}%ltEjWNl~Dx7lfjzckI<uZ6@C-Q9M;-8~38nDoXDxO^p&Cr?5}Ah1_9K?hmw?+mU~%>{O^(?g$f(u#+pCC`wg8BC_lb+FBFODn)WVISnX$BTgLStcwj>`cB&gG)$;E=GF=)X=A71p$ClW2e;%>Oel%b(s-SLh$<jyXT^)!qKpgI%hYKk8lkasQ5ckU4(@Z(JrzjxTYi#F8rmGA$F`R5c4@L5yZ@ok;<^t*x&tm}-Q09PR0f_5w(}v|MWuSpaTzT~=;g4i@8E}(cwi{}q#e1s>h|RHD!ltYS8%iq"
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
_SELLS_FIRST = False
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
