<div align="center">

# ProGuard: Towards Proactive Multimodal Safeguard

[Shaohan Yu](https://yushaohan.github.io/)<sup>1,2,3</sup>, 
[Lijun Li](https://adwardlee.github.io/)<sup>1,†</sup>, 
[Chenyang Si](https://chenyangsi.top/)<sup>2</sup>
[Lu Sheng](https://lucassheng.github.io/)<sup>3</sup>
[Jing Shao](https://amandajshao.github.io/)<sup>1,†</sup>

<sup>1</sup>[Shanghai Artificial Intelligence Laboratory](https://www.shlab.org.cn/), 
<sup>2</sup>[PRLab, Nanjing University](https://prlab-nju.com/), 
<sup>3</sup>[Beihang University](https://buaa.edu.cn/)

<!-- <sup>\*</sup>Equal Contribution,  -->
<sup>†</sup>Corresponding Author


[📄 Paper](#) (Coming Soon) | [🌐 Project Page](#) (Coming Soon) | [🤗 Model Weights](#) (Coming Soon) | [🤗 Datasets](#) (Coming Soon)

</div>

## 📝 Abstract

The rapid evolution of generative models has led to a continuous emergence of multimodal safety risks, exposing the limitations of existing defense methods. To address these challenges, we propose ProGuard, a vision-language proactive guard that identifies and describes out-of-distribution (OOD) safety risks without the need for model adjustments required by traditional reactive approaches. We first construct a modality-balanced dataset of 87K samples, each annotated with both binary safety labels and risk categories under a hierarchical multimodal safety taxonomy, effectively mitigating modality bias and ensuring consistent moderation across text, image, and text-image inputs. Based on this dataset, we train our vision-language base model purely through reinforcement learning (RL) to achieve efficient and concise reasoning. To approximate proactive safety scenarios in a controlled setting, we further introduce an OOD safety category inference task and augment the RL objective with a synonym-bank-based similarity reward that encourages the model to generate concise descriptions for unseen unsafe categories. Experimental results show that ProGuard achieves performance comparable to closed-source large models on binary safety classification, substantially outperforms existing open-source guard models on unsafe content categorization. Most notably, ProGuard delivers a strong proactive moderation ability, improving OOD risk detection by 52.6\% and OOD risk description by 64.8%.

<div align="center">
    <img src=./images/proguard.png width="100%">
</div>
<p align="center">

## 📣 News

[TODO]

- **[2025.12.date]** release our paper?

## 🔧 Usage

[TODO]

## 🙏 Acknowledgments

Our method are partly based on [verl](https://github.com/volcengine/verl) and [Qwen-VL series](https://github.com/QwenLM/Qwen3-VL). Thanks for their awesome works。



## 📖 Citation

