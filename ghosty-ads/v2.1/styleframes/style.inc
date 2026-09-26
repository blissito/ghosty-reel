<style>
      /* «Ghosty Ads — El colador». Piel de ghosty.studio (styleframes/frames.html) con acabado de caricatura plana:
         objetos SVG a mano con contorno de tinta y sombra DURA en lila claro. Sin gradientes, blur ni glow.
         Ghosty es SIEMPRE assets/ghosty.png (formmy.app/logo.png) sin tocar; sólo se anima con transforms. */
      :root {
        --bg: #f4f5fb; --dark: #191a20; --metal: #4b5563; --iron: #81838e; --outline: #e1e3e7; --white: #fff;
        --b100: #f5f5fc; --b200: #e4e4fa; --b300: #aeadef; --b500: #9a99ea; --b600: #8483e0; --b800: #161720;
        --bird: #edc75a; --cloud: #8ad7c9; --salmon: #e4ae8e; --grass: #7fbe60; --danger: #ed695f;
        --night: #23243a; --night2: #2e3050; --msg: #0a7cff; --hard: 8px 8px 0 #dcdcf6;
      }
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: 1080px; height: 1920px; overflow: hidden; background: var(--bg); font-family: "Inter", sans-serif; color: var(--dark); }
      #root { position: relative; width: 1080px; height: 1920px; overflow: hidden; background: var(--bg); }
      /* malla de rombos; recorre un módulo en todo el video (bucle que cierra sin salto) */
      #grid { position: absolute; left: -180px; top: -180px; width: 1440px; height: 2280px; opacity: .7; background-image:
          linear-gradient(45deg, transparent 47%, #e6e6f8 47%, #e6e6f8 53%, transparent 53%),
          linear-gradient(-45deg, transparent 47%, #e6e6f8 47%, #e6e6f8 53%, transparent 53%);
        background-size: 90px 90px; }
      .scene { position: absolute; inset: 0; display: none; }
      #s-hook { display: block; }
      .grp { position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; }
      .abs { position: absolute; display: block; }
      .h { visibility: hidden; }
      svg.o { position: absolute; overflow: visible; }

      .hl { position: absolute; left: 70px; top: 262px; font-family: "Poppins"; font-weight: 700; font-size: 80px; line-height: 1.04; letter-spacing: -.02em; width: 940px; }
      .hl span { color: var(--b600); }
      .hl .ib { display: inline-block; }
      .hl .num { display: inline-block; background: var(--danger); color: #fff; border-radius: 26px; padding: 0 22px; box-shadow: 6px 6px 0 var(--dark); }
      .chip { position: absolute; display: inline-flex; align-items: center; gap: 12px; background: #fff; border: 3px solid var(--dark); border-radius: 999px; padding: 8px 24px 8px 10px; font-family: "Poppins"; font-weight: 600; font-size: 36px; box-shadow: var(--hard); white-space: nowrap; }

      .ad { position: absolute; background: #fff; border: 3px solid var(--dark); border-radius: 36px; box-shadow: 10px 10px 0 var(--b300); overflow: hidden; }
      .ad .top { display: flex; align-items: center; gap: 14px; padding: 20px 22px; }
      .av { width: 58px; height: 58px; border-radius: 50%; background: var(--salmon); border: 3px solid var(--dark); display: grid; place-items: center; font-family: "Poppins"; font-weight: 700; font-size: 26px; flex: none; }
      .ad .top b { font-size: 28px; display: block; } .ad .top span { font-size: 21px; color: var(--iron); }
      .ad .pic { height: 330px; background: var(--b200); border-top: 3px solid var(--dark); border-bottom: 3px solid var(--dark); position: relative; }
      .ad .foot { display: flex; align-items: center; justify-content: space-between; padding: 18px 22px; }
      .ad .foot b { font-size: 25px; } .ad .foot span { display: block; font-size: 20px; color: var(--iron); }
      .send { display: inline-flex; align-items: center; gap: 10px; background: var(--msg); color: #fff; font-weight: 700; font-size: 26px; border-radius: 16px; padding: 14px 20px; border: 3px solid var(--dark); }

      .phone { position: absolute; background: var(--b800); border-radius: 64px; padding: 14px; box-shadow: 12px 12px 0 var(--b300); }
      .screen { position: relative; width: 100%; height: 100%; background: #fff; border-radius: 52px; overflow: hidden; }
      .screen.dark { background: var(--night); color: #eef0f6; }
      .notch { position: absolute; left: 50%; top: 14px; width: 120px; height: 30px; margin-left: -60px; border-radius: 20px; background: var(--b800); z-index: 3; }
      .badge { position: absolute; min-width: 110px; height: 110px; border-radius: 55px; background: var(--danger); color: #fff; border: 5px solid var(--dark); display: grid; place-items: center; font-family: "Poppins"; font-weight: 800; font-size: 58px; padding: 0 18px; z-index: 5; }
      .badge.gold { background: var(--bird); color: var(--dark); }
      .stack { position: absolute; left: 18px; right: 18px; top: 70px; }
      .nt { position: absolute; left: 0; right: 0; height: 74px; background: #eceef3; border-radius: 22px; padding: 12px 16px; display: flex; gap: 12px; align-items: center; font-size: 22px; }
      .nt i { flex: none; width: 40px; height: 40px; border-radius: 50%; background: var(--msg); display: grid; place-items: center; }
      .nt b { font-size: 21px; display: block; } .nt span { color: var(--metal); }
      .nt.buy { background: #fff6dc; border: 3px solid var(--bird); }

      .bub { position: absolute; font-size: 30px; font-weight: 600; padding: 16px 24px; border-radius: 30px; border: 3px solid var(--dark); background: #fff; white-space: nowrap; }
      .bub.gray { background: #eceef3; color: var(--metal); border-color: #b9bcc6; }
      .bub.gold { background: var(--bird); }
      .bub.lil { background: var(--b500); color: #fff; }
      .bub.tl { border-bottom-left-radius: 8px; } .bub.tr { border-bottom-right-radius: 8px; }

      .card { position: absolute; background: #fff; border: 3px solid var(--dark); border-radius: 30px; padding: 20px 24px; box-shadow: var(--hard); }
      .card h5 { font-family: "Poppins"; font-size: 30px; font-weight: 600; }
      .card p { font-size: 23px; color: var(--metal); margin-top: 4px; }
      .pill { display: inline-flex; align-items: center; gap: 8px; margin-top: 12px; font-size: 20px; font-weight: 700; text-transform: uppercase; letter-spacing: .04em; border-radius: 12px; padding: 5px 12px; }
      .pill.ok { background: #e3f3da; color: #3f7a24; } .pill.bad { background: #fde2df; color: #b8372d; } .pill.off { background: #eceef3; color: var(--metal); }

      /* chat grande (contesta / califica) */
      .chatc { position: absolute; background: #fff; border: 3px solid var(--dark); border-radius: 40px; box-shadow: 10px 10px 0 var(--b300); overflow: hidden; }
      .chatc .head { height: 96px; display: flex; align-items: center; gap: 14px; padding: 0 24px; border-bottom: 3px solid var(--outline); background: var(--b100); }
      .chatc .head b { font-size: 28px; display: block; } .chatc .head span { font-size: 20px; color: var(--iron); }
      .chatc .head svg { margin-left: auto; }
      .m { position: absolute; font-size: 27px; font-weight: 500; line-height: 1.28; padding: 16px 22px; border-radius: 28px; max-width: 420px; }
      .m.in { left: 22px; background: #eceef3; border-bottom-left-radius: 8px; }
      .m.out { right: 22px; background: var(--b500); color: #fff; border-bottom-right-radius: 8px; }
      .att { position: absolute; right: 22px; display: flex; align-items: center; gap: 16px; background: #fff; border: 3px solid var(--dark); border-radius: 24px; padding: 12px 20px 12px 14px; }
      .att b { font-size: 25px; display: block; } .att span { font-size: 23px; font-weight: 700; color: var(--grass); }

      /* tablero mini */
      .board { position: absolute; background: #fff; border: 3px solid var(--dark); border-radius: 30px; box-shadow: var(--hard); display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 14px; padding: 16px; }
      .col { background: #f2f5f9; border-radius: 20px; padding: 10px 12px; position: relative; }
      .col h6 { font-size: 20px; font-weight: 700; color: var(--metal); display: flex; align-items: center; gap: 8px; }
      .col h6 i { width: 12px; height: 12px; border-radius: 50%; }
      .mini { margin-top: 8px; background: #fff; border: 2px solid var(--outline); border-radius: 14px; padding: 8px 12px; font-size: 19px; font-weight: 600; }
      .mini.hot { border: 3px solid var(--bird); background: #fff6dc; }
      .slot { margin-top: 8px; height: 46px; border: 2px dashed #c9cbd3; border-radius: 14px; }

      /* reporte */
      .lock { text-align: center; padding-top: 80px; }
      .lock .d { font-size: 26px; color: #b9bbd3; font-weight: 500; }
      .lock .hh { font-family: "Poppins"; font-weight: 700; font-size: 130px; line-height: 1; margin-top: 6px; position: relative; height: 130px; }
      .lock .hh div { position: absolute; left: 0; right: 0; }
      .push { position: absolute; left: 20px; right: 20px; top: 330px; background: #fff; color: var(--dark); border-radius: 34px; padding: 22px; border: 3px solid var(--dark); }
      .push .ph { display: flex; gap: 14px; align-items: center; }
      .push .ph img { width: 54px; }
      .push .ph b { font-size: 25px; display: block; } .push .ph span { font-size: 19px; color: var(--iron); }
      .push .kpi { display: flex; gap: 10px; margin: 16px 0 10px; }
      .push .kpi div { flex: 1; background: var(--b100); border-radius: 18px; padding: 10px; text-align: center; font-size: 18px; color: var(--metal); font-weight: 600; }
      .push .kpi div b { display: block; font-family: "Poppins"; font-size: 40px; color: var(--dark); line-height: 1.1; }
      .push .row { display: flex; gap: 12px; align-items: flex-start; padding: 12px 4px; border-top: 2px solid var(--outline); font-size: 21px; line-height: 1.3; }
      .push .row i { flex: none; width: 16px; height: 16px; border-radius: 50%; margin-top: 7px; }

      /* CTA */
      .cta { position: absolute; background: #fff; border: 3px solid var(--dark); border-radius: 44px; box-shadow: 10px 10px 0 var(--b300); padding: 44px 44px 40px; text-align: center; }
      .cta .btn { display: inline-flex; align-items: center; gap: 16px; background: var(--msg); color: #fff; font-weight: 700; font-size: 44px; border-radius: 999px; padding: 20px 40px 20px 22px; border: 4px solid var(--dark); }
      .cta .url { margin-top: 30px; font-family: "Poppins"; font-weight: 700; font-size: 50px; }
      .cta .date { margin-top: 22px; display: inline-block; background: var(--bird); border: 3px solid var(--dark); border-radius: 16px; padding: 8px 20px; font-weight: 800; font-size: 34px; }

      /* karaoke: una sola línea, 72 px, en pastilla de tinta; dichas en blanco, actual en lila, por decir en gris */
      #cap { position: absolute; left: 60px; width: 860px; top: 1262px; height: 118px; z-index: 50; }
      .capPill { position: absolute; left: 0; top: 0; width: 860px; height: 118px; visibility: hidden; background: var(--dark); border-radius: 30px; display: flex; align-items: center; justify-content: center; gap: 18px; font-family: "Poppins"; font-weight: 700; font-size: 72px; line-height: 1; white-space: nowrap; }
      .capPill b { font-weight: 700; color: #6b6e7c; }
      #measure { position: absolute; left: 0; top: 0; visibility: hidden; font-family: "Poppins"; font-weight: 700; font-size: 72px; white-space: nowrap; }

      /* cortinilla: rebanadas sesgadas con back.out y el glifo que sella el corte */
      .slice { position: absolute; left: 0; top: -340px; width: 2200px; height: 2600px; z-index: 90; visibility: hidden; border-left: 6px solid var(--dark); }
      #seal { position: absolute; left: 290px; top: 710px; width: 500px; height: 500px; border-radius: 110px; background: #fff; border: 6px solid var(--dark); box-shadow: 14px 14px 0 var(--b300); display: grid; place-items: center; z-index: 95; visibility: hidden; }
      #seal svg { position: absolute; left: 50%; top: 50%; overflow: visible; }
      #seal .g { visibility: hidden; }
      #seal .three { position: absolute; inset: 0; display: grid; place-items: center; font-family: "Poppins"; font-weight: 800; font-size: 330px; color: var(--dark); background: var(--bird); border-radius: 104px; }
    </style>