FasdUAS 1.101.10   ��   ��    k             l      ��  ��    � �
This script will walk through every selected contact in the Address Book 
and remove spaces in any phone numbers that it finds.
     � 	 	 
 T h i s   s c r i p t   w i l l   w a l k   t h r o u g h   e v e r y   s e l e c t e d   c o n t a c t   i n   t h e   A d d r e s s   B o o k   
 a n d   r e m o v e   s p a c e s   i n   a n y   p h o n e   n u m b e r s   t h a t   i t   f i n d s . 
   
  
 l     ��������  ��  ��        l    \ ����  O     \    k    [       I   	������
�� .miscactvnull��� ��� null��  ��     ��  X   
 [ ��   X    V ��   k   . Q       r   . <    n   . 8    I   / 8��  ���� 0 replacetext ReplaceText    ! " ! n   / 2 # $ # 1   0 2��
�� 
az17 $ o   / 0���� 0 
this_phone   "  % & % m   2 3 ' ' � ( (   &  )�� ) m   3 4 * * � + +  ��  ��     f   . /  l      ,���� , n       - . - 1   9 ;��
�� 
az17 . o   8 9���� 0 
this_phone  ��  ��     / 0 / r   = K 1 2 1 n   = G 3 4 3 I   > G�� 5���� 0 replacetext ReplaceText 5  6 7 6 n   > A 8 9 8 1   ? A��
�� 
az17 9 o   > ?���� 0 
this_phone   7  : ; : m   A B < < � = =  - ;  >�� > m   B C ? ? � @ @  ��  ��   4  f   = > 2 l      A���� A n       B C B 1   H J��
�� 
az17 C o   G H���� 0 
this_phone  ��  ��   0  D�� D I  L Q������
�� .coresavenull���     null��  ��  ��  �� 0 
this_phone    n    " E F E 2     "��
�� 
az20 F o     ���� 0 this_person  �� 0 this_person    l    G���� G 2    ��
�� 
azf4��  ��  ��    m      H H�                                                                                  adrb  alis    f  Macintosh HD               �<�H+     YAddress Book.app                                                9-�,\�        ����  	                Applications    �<q      �+�J       Y  +Macintosh HD:Applications: Address Book.app   "  A d d r e s s   B o o k . a p p    M a c i n t o s h   H D  Applications/Address Book.app   / ��  ��  ��     I J I l     ��������  ��  ��   J  K�� K i      L M L I      �� N���� 0 replacetext ReplaceText N  O P O o      ���� 0 	thestring 	theString P  Q R Q o      ���� 0 fstring fString R  S�� S o      ���� 0 rstring rString��  ��   M k     & T T  U V U r      W X W n      Y Z Y 1    ��
�� 
txdl Z 1     ��
�� 
ascr X o      ���� (0 current_delimiters current_Delimiters V  [ \ [ r     ] ^ ] o    ���� 0 fstring fString ^ n      _ ` _ 1    
��
�� 
txdl ` 1    ��
�� 
ascr \  a b a r     c d c n     e f e 2    ��
�� 
citm f o    ���� 0 	thestring 	theString d o      ���� 0 slist sList b  g h g r     i j i o    ���� 0 rstring rString j n      k l k 1    ��
�� 
txdl l 1    ��
�� 
ascr h  m n m r     o p o c     q r q o    ���� 0 slist sList r m    ��
�� 
TEXT p o      ���� 0 	newstring 	newString n  s t s r    # u v u o    ���� (0 current_delimiters current_Delimiters v n      w x w 1     "��
�� 
txdl x 1     ��
�� 
ascr t  y�� y L   $ & z z o   $ %���� 0 	newstring 	newString��  ��       �� { | }��   { ������ 0 replacetext ReplaceText
�� .aevtoappnull  �   � **** | �� M���� ~ ���� 0 replacetext ReplaceText�� �� ���  �  �������� 0 	thestring 	theString�� 0 fstring fString�� 0 rstring rString��   ~ �������������� 0 	thestring 	theString�� 0 fstring fString�� 0 rstring rString�� (0 current_delimiters current_Delimiters�� 0 slist sList�� 0 	newstring 	newString  ��������
�� 
ascr
�� 
txdl
�� 
citm
�� 
TEXT�� '��,E�O���,FO��-E�O���,FO��&E�O���,FO� } �� ����� � ���
�� .aevtoappnull  �   � **** � k     \ � �  ����  ��  ��   � ������ 0 this_person  �� 0 
this_phone   �  H�������������� ' *�� < ?��
�� .miscactvnull��� ��� null
�� 
azf4
�� 
kocl
�� 
cobj
�� .corecnte****       ****
�� 
az20
�� 
az17�� 0 replacetext ReplaceText
�� .coresavenull���     null�� ]� Y*j O P*�-[��l kh   9��-[��l kh )��,��m+ 
��,FO)��,��m+ 
��,FO*j [OY��[OY��U ascr  ��ޭ