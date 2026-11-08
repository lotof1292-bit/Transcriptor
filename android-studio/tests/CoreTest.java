package mx.transcriptor.studio;
import java.io.*;import java.util.*;
public class CoreTest {
 static int tests=0;static void ok(boolean b,String why){if(!b)throw new AssertionError(why);tests++;}
 public static void main(String[] args)throws Exception {
 String source="María pagó $7,500 el 1 de noviembre de 2026 en Mérida. Ana no llegó.";
 TextTools.Protection p=TextTools.protect(source,Arrays.asList("María","Mérida","Ana"));
 ok(p.restore(p.masked).equals(source),"Protection must round-trip exactly");ok(!p.masked.contains("2026"),"Date remains unmasked");ok(!p.masked.contains("7,500"),"Amount remains unmasked");ok(p.problems(p.masked).isEmpty(),"Unchanged locks rejected");String token=p.values.keySet().iterator().next();ok(!p.problems(p.masked.replace(token,"")).isEmpty(),"Missing name not detected");ok(!p.problems(p.masked+token).isEmpty(),"Duplicated name not detected");ok(!p.problems(p.masked+"ZXQKEEP999QXZ").isEmpty(),"Unknown lock not detected");
 ok(TextTools.replace("Ana banana ANA","Ana","$1\\",true,false).equals("$1\\ banana $1\\"),"Whole word / literal replacement");ok(TextTools.replace("ÁNA ána","ána","x",true,false).equals("x x"),"Unicode case folding");
 String unicode=String.join("",Collections.nCopies(2000,"á😀 palabra. "));List<String> chunks=TextTools.chunks(unicode,300);ok(String.join("",chunks).equals(unicode),"Chunking dropped text");for(String c:chunks){ok(c.length()<=300,"Chunk oversized");ok(!Character.isHighSurrogate(c.charAt(c.length()-1)),"Split surrogate");}
 File dir=new File(args[0]);dir.mkdirs();File a=new File(dir,"a.wav"),b=new File(dir,"b.wav"),out=new File(dir,"out.wav");wave(a,16000,1600);wave(b,16000,3200);WavFiles.join(Arrays.asList(a,b),out,100);WavFiles.Piece piece=WavFiles.inspect(out);ok(piece.size==1600+3200+3200,"Silence or audio bytes lost");ok(out.length()==44+piece.size,"Invalid RIFF length");wave(b,24000,3200);boolean rejected=false;try{WavFiles.join(Arrays.asList(a,b),out,0);}catch(IOException e){rejected=true;}ok(rejected,"Mixed sample rates accepted");System.out.println("PASS "+tests+" checks: locks, Unicode, replacements, chunking and WAV output");
 }
 static void wave(File f,int rate,int bytes)throws Exception{try(OutputStream o=new FileOutputStream(f)){o.write("RIFF".getBytes("US-ASCII"));WavFiles.word(o,36+bytes);o.write("WAVEfmt ".getBytes("US-ASCII"));WavFiles.word(o,16);o.write(new byte[]{1,0,1,0});WavFiles.word(o,rate);WavFiles.word(o,rate*2);o.write(new byte[]{2,0,16,0});o.write("data".getBytes("US-ASCII"));WavFiles.word(o,bytes);o.write(new byte[bytes]);}}
}
